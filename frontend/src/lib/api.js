// Client API. Il frontend NON calcola importi né ammissibilità: invia dati e mostra il JSON del server.
const BASE = (import.meta.env.VITE_API_BASE || '/api/v2').replace(/\/$/, '')

export class ApiError extends Error {
  constructor(status, detail) {
    super(typeof detail === 'string' ? detail : detail?.message || `Errore ${status}`)
    this.status = status
    this.detail = detail
  }
}

async function call(path, options) {
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
      detail = Array.isArray(body.detail) ? body.detail.map((d) => d.msg).join('; ') : body.detail ?? detail
    } catch { /* corpo non JSON */ }
    throw new ApiError(res.status, detail)
  }
  return res
}

const post = (path, body) =>
  call(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }).then((r) => r.json())

const blob = async (path, body) =>
  (await call(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })).blob()

export const api = {
  validateBudget: (req) => post('/budget/validate', req),
  exportXlsx: (req) => blob('/budget/export/xlsx', req),
  exportPdf: (req) => blob('/budget/export/pdf', req),
  matchPattern: (body) => post('/pattern/match', body),
  optimizeAllocation: (body) => post('/allocation/optimize', body),
  register: (body) => post('/registry/register', body),
  registryStatus: () => call('/registry/status').then((r) => r.json()),
  verifyRoot: (projectId, root) => call(`/registry/verify/${encodeURIComponent(projectId)}?merkle_root=${encodeURIComponent(root)}`).then((r) => r.json()),
  verifyRecompute: (body) => post('/registry/verify/recompute', body),
  // ingestione Fonte A (pannello interno)
  ingestionCatalog: () => call('/ingestion/catalog').then((r) => r.json()),
  ingestionAddBando: (body) => post('/ingestion/catalog', body),
  ingestionConfirm: (id) => post(`/ingestion/confirm/${encodeURIComponent(id)}`, {}),
  ingestionExtract: (body) => post('/ingestion/extract', body),
  ingestionStatus: (id) => call(`/ingestion/status/${encodeURIComponent(id)}`).then((r) => r.json()),
  ingestionQueue: () => call('/ingestion/review-queue').then((r) => r.json()),
  ingestionReview: (body) => post('/ingestion/review', body),
  ingestionRules: (id) => call(`/ingestion/grant-rules/${encodeURIComponent(id)}`).then((r) => r.json()),
}

export function download(blobData, filename) {
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blobData)
  a.download = filename
  a.click()
  URL.revokeObjectURL(a.href)
}
