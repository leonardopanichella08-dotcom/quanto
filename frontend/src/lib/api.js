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

// Sessione: token e utente restano solo per la durata della scheda del browser (sessionStorage).
const TOKEN_KEY = 'quanto_token'
const USER_KEY = 'quanto_user'
const read = (k) => { try { return sessionStorage.getItem(k) } catch { return null } }
export const session = {
  token: () => read(TOKEN_KEY),
  user: () => { try { return JSON.parse(read(USER_KEY) || 'null') } catch { return null } },
  set: (token, user) => { try { sessionStorage.setItem(TOKEN_KEY, token); sessionStorage.setItem(USER_KEY, JSON.stringify(user)) } catch { /* sessionStorage non disponibile */ } },
  clear: () => { try { sessionStorage.removeItem(TOKEN_KEY); sessionStorage.removeItem(USER_KEY) } catch { /* idem */ } },
}
export const hqToken = { get: session.token, set: () => {}, clear: session.clear }   // compatibilità: il Quartier Generale usa il token dell'utente manager

// Il lavoro (azienda cliente) su cui sta lavorando lo studio: ogni chiamata ne porta l'identificativo, così profilo, bilanci, documenti e risultati sono sempre quelli giusti.
let activeClientId = null
export const workspace = {
  id: () => activeClientId,
  set: (id) => { activeClientId = id },
  remembered: (user) => { try { return Number(localStorage.getItem(`quanto_client_${user?.email}`)) || null } catch { return null } },
  remember: (user, id) => { try { if (id) localStorage.setItem(`quanto_client_${user?.email}`, String(id)); else localStorage.removeItem(`quanto_client_${user?.email}`) } catch { /* localStorage non disponibile */ } },
}

async function call(path, options = {}) {
  let res
  const token = session.token()
  const headers = { ...(token ? { Authorization: `Bearer ${token}` } : {}), ...(activeClientId ? { 'X-Client-Id': String(activeClientId) } : {}), ...(options.headers || {}) }
  try {
    res = await fetch(`${BASE}${path}`, { ...options, headers })
  } catch {
    throw new ApiError(0, 'Backend non raggiungibile. Avviare uvicorn su :8000.')
  }
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = Array.isArray(body.detail) ? body.detail.map((d) => `${(d.loc || []).slice(1).join('.')}: ${d.msg}`).join('; ') : body.detail ?? detail
    } catch { /* corpo non JSON */ }
    if (res.status === 401 && token && !path.startsWith('/auth/login')) { session.clear(); window.dispatchEvent(new Event('quanto-logout')) }   // sessione scaduta o revocata
    throw new ApiError(res.status, detail)
  }
  return res
}

const json = { 'Content-Type': 'application/json' }
const post = (path, body, headers = {}) => call(path, { method: 'POST', headers: { ...json, ...headers }, body: JSON.stringify(body) }).then((r) => r.json())
const blob = async (path, body) => (await call(path, { method: 'POST', headers: json, body: JSON.stringify(body) })).blob()

// HQ: ogni chiamata porta il token; se scade (401) il chiamante torna al cancello.
const hqGet = (path) => call(`/hq${path}`, { headers: { 'X-HQ-Token': hqToken.get() || '' } }).then((r) => r.json())
const hqSend = (method, path, body) => call(`/hq${path}`, {
  method, headers: { 'X-HQ-Token': hqToken.get() || '', ...(body !== undefined ? json : {}) }, ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
}).then((r) => r.json())
const hqBlob = (path) => call(`/hq${path}`, { headers: { 'X-HQ-Token': hqToken.get() || '' } }).then((r) => r.blob())

// Fonte B: lettura per tutti, scrittura per il manager (stesso gettone del Quartier Generale)
const fbHeaders = () => ({ 'X-HQ-Token': hqToken.get() || '' })
const fbGet = (path) => call(`/fonte-b${path}`, { headers: fbHeaders() }).then((r) => r.json())
const fbSend = (method, path, body) => call(`/fonte-b${path}`, { method, headers: { ...fbHeaders(), ...(body !== undefined ? json : {}) }, ...(body !== undefined ? { body: JSON.stringify(body) } : {}) }).then((r) => r.json())

export const api = {
  login: (email, password) => post('/auth/login', { email, password }),
  register: (email, name, password) => post('/auth/register', { email, name, password }),
  changePassword: (current_password, new_password) => post('/auth/change-password', { current_password, new_password }),
  meProfile: () => call('/auth/me/profile').then((r) => r.json()),
  updateMe: (body) => call('/auth/me', { method: 'PATCH', headers: json, body: JSON.stringify(body) }).then((r) => r.json()),
  signOutEverywhere: () => post('/auth/me/sign-out-everywhere', {}),
  exportMe: () => call('/auth/me/export').then((r) => r.blob()),
  deleteMe: (password, confirm_email) => call('/auth/me', { method: 'DELETE', headers: json, body: JSON.stringify({ password, confirm_email }) }).then((r) => r.json()),
  meActivity: (limit = 30) => call(`/auth/me/activity?limit=${limit}`).then((r) => r.json()),
  meCredits: () => call('/auth/me/credits').then((r) => r.json()),
  users: () => hqGet('/users'),
  createUser: (body) => hqSend('POST', '/users', body),
  patchUser: (id, body) => hqSend('PATCH', `/users/${id}`, body),
  // Fonte C: documenti del cliente
  fcDocuments: () => call('/fonte-c/documents').then((r) => r.json()),
  fcDocument: (id) => call(`/fonte-c/documents/${id}`).then((r) => r.json()),
  fcUpload: (body) => post('/fonte-c/documents', body),
  fcDelete: (id) => call(`/fonte-c/documents/${id}`, { method: 'DELETE' }).then((r) => r.json()),
  fcFile: (id) => call(`/fonte-c/documents/${id}/file`).then((r) => r.blob()),
  fcReview: (docId, fieldId, action, value) => post(`/fonte-c/documents/${docId}/fields/${fieldId}/review`, { action, value }),
  fcCostLine: (id) => call(`/fonte-c/documents/${id}/cost-line`).then((r) => r.json()),
  fcExpenses: (id) => call(`/fonte-c/documents/${id}/expenses`).then((r) => r.json()),
  fcDraftItems: (id) => call(`/fonte-c/documents/${id}/draft-items`).then((r) => r.json()),
  // fondi per l'allocazione
  funds: () => call('/allocation/funds').then((r) => r.json()),
  deriveFund: (body) => post('/allocation/funds/from-bando', body),
  deleteFund: (id) => call(`/allocation/funds/${encodeURIComponent(id)}`, { method: 'DELETE' }).then((r) => r.json()),
  fonteBSummary: () => call('/fonte-b/summary').then((r) => r.json()),
  fbKinds: () => fbGet('/kinds'),
  fbDatasets: () => fbGet('/datasets'),
  fbDataset: (id) => fbGet(`/datasets/${id}`),
  fbUpload: (body) => fbSend('POST', '/datasets', body),
  fbPublish: (id, attest) => fbSend('POST', `/datasets/${id}/publish`, { attest_official: attest }),
  fbDelete: (id) => fbSend('DELETE', `/datasets/${id}`),
  fbFile: (id) => call(`/fonte-b/datasets/${id}/file`, { headers: fbHeaders() }).then((r) => r.blob()),
  fbTemplate: (kind) => call(`/fonte-b/template/${kind}.csv`, { headers: fbHeaders() }).then((r) => r.blob()),
  // --- bandi
  bandi: () => call('/bandi').then((r) => r.json()),
  bandoDetail: (id) => call(`/bandi/${encodeURIComponent(id)}`).then((r) => r.json()),
  bandoSelect: (id) => post(`/bandi/${encodeURIComponent(id)}/select`, {}),
  bandoReferences: () => call('/bandi/references').then((r) => r.json()),
  bandiSearch: (q) => call(`/bandi/search?q=${encodeURIComponent(q)}`).then((r) => r.json()),
  bandiCatalog: ({ q = '', issuer = '', onlyNew = false, page = 1, pageSize = 30, described = null, withMeta = false } = {}) => {
    const p = new URLSearchParams({ page: String(page), page_size: String(pageSize) })
    if (q) p.set('q', q)
    if (issuer) p.set('issuer', issuer)
    if (onlyNew) p.set('only_new', 'true')
    if (described !== null) p.set('described', String(described))
    if (withMeta) p.set('with_meta', 'true')
    return call(`/bandi/catalog?${p}`).then((r) => r.json())
  },
  bandiCatalogStats: () => call('/bandi/catalog/stats').then((r) => r.json()),
  catalogDescribe: (limit = 120) => call(`/cron/catalog-describe?limit=${limit}`, { method: 'POST' }).then((r) => r.json()),
  bandiCatalogIssuers: () => call('/bandi/catalog/issuers').then((r) => r.json()),
  researchConfirm: (body) => post('/bandi/research/confirm', body),
  researchSearch: (body) => post('/bandi/research/search', body),
  researchFetch: (body) => post('/bandi/research/fetch', body),
  researchAnalyze: (body) => post('/bandi/research/analyze', body),
  researchRun: (body) => post('/bandi/research/run', body),
  sourceText: (bandoId, sha) => call(`/bandi/${encodeURIComponent(bandoId)}/sources/${encodeURIComponent(sha)}`).then((r) => r.json()),
  // --- missione uno
  fields: () => call('/budget/fields').then((r) => r.json()),
  criteria: () => call('/budget/criteria').then((r) => r.json()),
  importItems: (body) => post('/budget/import', body),
  templateUrl: `${BASE}/budget/template.xlsx`,
  validateBudget: (req) => post('/budget/validate', req),
  exportXlsx: (req) => blob('/budget/export/xlsx', req),
  exportPdf: (req) => blob('/budget/export/pdf', req),
  merkleLab: (rows, prove_index) => post('/registry/merkle-lab', { rows, ...(prove_index != null ? { prove_index } : {}) }),
  // --- altre missioni
  matchPattern: (body) => post('/pattern/match', body),
  templateMeta: () => call('/templates/meta').then((r) => r.json()),
  templatesMine: () => call('/templates').then((r) => r.json()),
  templateNiches: (engine = 'COLLETTIVO') => call(`/templates/niches?engine=${engine}`).then((r) => r.json()),
  templateLearning: (engine = 'COLLETTIVO') => call(`/templates/learning?engine=${engine}`).then((r) => r.json()),
  templateRecommend: (body) => post('/templates/recommend', body),
  createTemplate: (body) => post('/templates', body),
  patchTemplate: (id, body) => call(`/templates/${id}`, { method: 'PATCH', headers: json, body: JSON.stringify(body) }).then((r) => r.json()),
  deleteTemplate: (id) => call(`/templates/${id}`, { method: 'DELETE' }).then((r) => r.json()),
  patternCategories: () => call('/pattern/categories').then((r) => r.json()),
  patternBudgets: () => call('/pattern/budgets').then((r) => r.json()),
  patternImport: (body) => post('/pattern/import', body),
  catalogRefresh: () => call('/cron/catalog-refresh', { method: 'POST' }).then((r) => r.json()),
  optimizeAllocation: (body) => post('/allocation/optimize', body),
  wpPlan: (body) => post('/budget/wp-plan', body),
  // profilo aziendale: dati e bilanci per esercizio, stima dell'anno dopo, bandi adatti, bozza di budget
  profile: () => call('/profile').then((r) => r.json()),
  saveProfile: (fields) => call('/profile', { method: 'PUT', headers: json, body: JSON.stringify({ fields }) }).then((r) => r.json()),
  saveFinancials: (year, values) => call(`/profile/financials/${year}`, { method: 'PUT', headers: json, body: JSON.stringify({ values }) }).then((r) => r.json()),
  profileSync: () => post('/profile/sync', {}),
  profileForecast: (year, growth) => post('/profile/forecast', { year, growth }),
  profileMatch: (year, growth) => post('/profile/match', { year, growth }),
  clients: () => call('/clients').then((r) => r.json()),
  createClient: (name, note = '') => post('/clients', { name, note }),
  patchClient: (id, body) => call(`/clients/${id}`, { method: 'PATCH', headers: json, body: JSON.stringify(body) }).then((r) => r.json()),
  deleteClient: (id, confirm) => call(`/clients/${id}?confirm=${encodeURIComponent(confirm)}`, { method: 'DELETE' }).then((r) => r.json()),
  clientState: (key) => call(`/clients/current/state/${key}`).then((r) => r.json()),
  saveClientState: (key, value) => call(`/clients/current/state/${key}`, { method: 'PUT', headers: json, body: JSON.stringify({ value }) }).then((r) => r.json()),
  forecastTemplate: () => call('/profile/forecast-template').then((r) => r.json()),
  saveForecastTemplate: (growth, label, note) => call('/profile/forecast-template', { method: 'PUT', headers: json, body: JSON.stringify({ growth, label, note }) }).then((r) => r.json()),
  deleteForecastTemplate: () => call('/profile/forecast-template', { method: 'DELETE' }).then((r) => r.json()),
  profileTemplate: (bando_id, scale_pct, fit) => post('/profile/template', { bando_id, scale_pct, fit }),
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
  hqManual: () => hqGet('/manual'),
  hqManualPdf: () => hqBlob('/manual.pdf'),
  hqOperations: () => hqGet('/operations'),
  hqTimeline: (params = {}) => hqGet(`/timeline?${new URLSearchParams(Object.entries(params).filter(([, v]) => v)).toString()}`),
  hqRun: (id) => hqGet(`/runs/${id}`),
  hqProjects: () => hqGet('/projects'),
  hqProject: (id) => hqGet(`/projects/${encodeURIComponent(id)}`),
  hqBando: (id) => hqGet(`/bandi/${encodeURIComponent(id)}`),
  hqDocuments: (kind) => hqGet(`/documents${kind ? `?kind=${kind}` : ''}`),
  hqTables: () => hqGet('/db/tables'),
  hqRows: (table, limit, offset) => hqGet(`/db/table/${table}?limit=${limit}&offset=${offset}`),
  // --- archivio bandi (gestione dati del manager)
  hqArchive: () => hqGet('/archive'),
  hqArchiveDetail: (id) => hqGet(`/archive/${encodeURIComponent(id)}`),
  hqConsultant: (id) => hqGet(`/archive/${encodeURIComponent(id)}/consultant`),
  hqSourceText: (id, sha) => hqGet(`/archive/${encodeURIComponent(id)}/sources/${sha}/text`),
  hqSourceFile: (id, sha, dl) => hqBlob(`/archive/${encodeURIComponent(id)}/sources/${sha}/file${dl ? '?download=true' : ''}`),
  hqDeleteSource: (id, sha) => hqSend('DELETE', `/archive/${encodeURIComponent(id)}/sources/${sha}`),
  hqReanalyze: (id) => hqSend('POST', `/archive/${encodeURIComponent(id)}/reanalyze`),
  hqSetRule: (id, key, value) => hqSend('PUT', `/archive/${encodeURIComponent(id)}/rules/${key}`, { value }),
  hqDeleteRule: (id, key) => hqSend('DELETE', `/archive/${encodeURIComponent(id)}/rules/${key}`),
  hqAddRequirement: (id, body) => hqSend('POST', `/archive/${encodeURIComponent(id)}/requirements`, body),
  hqPatchRequirement: (id, seq, body) => hqSend('PATCH', `/archive/${encodeURIComponent(id)}/requirements/${seq}`, body),
  hqDeleteRequirement: (id, seq) => hqSend('DELETE', `/archive/${encodeURIComponent(id)}/requirements/${seq}`),
  hqRenameBando: (id, name) => hqSend('PATCH', `/archive/${encodeURIComponent(id)}`, { name }),
  hqDeleteBando: (id) => hqSend('DELETE', `/archive/${encodeURIComponent(id)}`),
  hqRestoreDefaults: () => hqSend('POST', '/archive/restore-defaults'),
  hqExportBando: (id) => hqBlob(`/archive/${encodeURIComponent(id)}/export.zip`),
  hqDeleteRow: (table, rowid) => hqSend('DELETE', `/db/table/${table}/row/${rowid}`),
  hqClearTable: (table) => hqSend('DELETE', `/db/table/${table}?confirm=${table}`),
  hqExportTable: (table) => hqBlob(`/db/table/${table}/export.csv`),
}

// Il link va agganciato alla pagina prima del clic (alcuni browser integrati ignorano un link «staccato») e l'indirizzo temporaneo non si revoca subito.
export function download(blobData, filename) {
  const typed = blobData.type ? blobData : new Blob([blobData], { type: filename.endsWith('.pdf') ? 'application/pdf' : 'application/octet-stream' })
  const url = URL.createObjectURL(typed)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.rel = 'noopener'
  a.style.display = 'none'
  document.body.appendChild(a)
  a.click()
  setTimeout(() => { a.remove(); URL.revokeObjectURL(url) }, 30000)
}

export function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result).split(',')[1])
    reader.onerror = () => reject(new Error('Impossibile leggere il file'))
    reader.readAsDataURL(file)
  })
}
