// Client API. Il frontend NON calcola importi né ammissibilità: invia dati e mostra il JSON del server.
const BASE = (import.meta.env.VITE_API_BASE || '/api/v2').replace(/\/$/, '')
const HQ_KEY = 'quanto_hq_token'

export class ApiError extends Error {
  constructor(status, detail) {
    super(typeof detail === 'string' ? detail : detail?.message || `Errore ${status}`)
    this.status = status
    this.detail = detail
  }
}

export const hqToken = {
  get: () => { try { return sessionStorage.getItem(HQ_KEY) } catch { return null } },
  set: (t) => { try { sessionStorage.setItem(HQ_KEY, t) } catch { /* sessionStorage non disponibile */ } },
  clear: () => { try { sessionStorage.removeItem(HQ_KEY) } catch { /* idem */ } },
}

async function call(path, options = {}) {
  let res
  try {
    res = await fetch(`${BASE}${path}`, options)
  } catch {
    throw new ApiError(0, 'Backend non raggiungibile. Avviare uvicorn su :8000.')
  }
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = Array.isArray(body.detail) ? body.detail.map((d) => `${(d.loc || []).slice(1).join('.')}: ${d.msg}`).join('; ') : body.detail ?? detail
    } catch { /* corpo non JSON */ }
    throw new ApiError(res.status, detail)
  }
  return res
}

const json = { 'Content-Type': 'application/json' }
const post = (path, body, headers = {}) => call(path, { method: 'POST', headers: { ...json, ...headers }, body: JSON.stringify(body) }).then((r) => r.json())
const blob = async (path, body) => (await call(path, { method: 'POST', headers: json, body: JSON.stringify(body) })).blob()

// HQ: ogni chiamata porta il token; se scade (401) il chiamante torna al cancello.
const hqGet = (path) => call(`/hq${path}`, { headers: { 'X-HQ-Token': hqToken.get() || '' } }).then((r) => r.json())

export const api = {
  // --- bandi
  bandi: () => call('/bandi').then((r) => r.json()),
  bandoDetail: (id) => call(`/bandi/${encodeURIComponent(id)}`).then((r) => r.json()),
  bandoSelect: (id) => post(`/bandi/${encodeURIComponent(id)}/select`, {}),
  bandoReferences: () => call('/bandi/references').then((r) => r.json()),
  bandoUpload: (body) => post('/bandi/upload', body),
  // --- missione uno
  fields: () => call('/budget/fields').then((r) => r.json()),
  criteria: () => call('/budget/criteria').then((r) => r.json()),
  demo: (bandoId, mode) => call(`/budget/demo?bando_id=${encodeURIComponent(bandoId)}&mode=${mode}`).then((r) => r.json()),
  importItems: (body) => post('/budget/import', body),
  templateUrl: `${BASE}/budget/template.xlsx`,
  validateBudget: (req) => post('/budget/validate', req),
  exportXlsx: (req) => blob('/budget/export/xlsx', req),
  exportPdf: (req) => blob('/budget/export/pdf', req),
  // --- altre missioni
  matchPattern: (body) => post('/pattern/match', body),
  optimizeAllocation: (body) => post('/allocation/optimize', body),
  register: (body) => post('/registry/register', body),
  registryStatus: () => call('/registry/status').then((r) => r.json()),
  verifyRoot: (projectId, root) => call(`/registry/verify/${encodeURIComponent(projectId)}?merkle_root=${encodeURIComponent(root)}`).then((r) => r.json()),
  verifyRecompute: (body) => post('/registry/verify/recompute', body),
  // --- ingestione (uso interno, dentro l'HQ)
  ingestionAddBando: (body) => post('/ingestion/catalog', body),
  ingestionConfirm: (id) => post(`/ingestion/confirm/${encodeURIComponent(id)}`, {}),
  ingestionExtract: (body) => post('/ingestion/extract', body),
  ingestionStatus: (id) => call(`/ingestion/status/${encodeURIComponent(id)}`).then((r) => r.json()),
  ingestionQueue: () => call('/ingestion/review-queue').then((r) => r.json()),
  ingestionReview: (body) => post('/ingestion/review', body),
  ingestionRules: (id) => call(`/ingestion/grant-rules/${encodeURIComponent(id)}`).then((r) => r.json()),
  // --- quartier generale
  hqLogin: (code) => post('/hq/login', { code }),
  hqOverview: () => hqGet('/overview'),
  hqOperations: () => hqGet('/operations'),
  hqTimeline: (params = {}) => hqGet(`/timeline?${new URLSearchParams(Object.entries(params).filter(([, v]) => v)).toString()}`),
  hqRun: (id) => hqGet(`/runs/${id}`),
  hqProjects: () => hqGet('/projects'),
  hqProject: (id) => hqGet(`/projects/${encodeURIComponent(id)}`),
  hqBando: (id) => hqGet(`/bandi/${encodeURIComponent(id)}`),
  hqDocuments: (kind) => hqGet(`/documents${kind ? `?kind=${kind}` : ''}`),
  hqTables: () => hqGet('/db/tables'),
  hqRows: (table, limit, offset) => hqGet(`/db/table/${table}?limit=${limit}&offset=${offset}`),
}

export function download(blobData, filename) {
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blobData)
  a.download = filename
  a.click()
  URL.revokeObjectURL(a.href)
}

export function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result).split(',')[1])
    reader.onerror = () => reject(new Error('Impossibile leggere il file'))
    reader.readAsDataURL(file)
  })
}
