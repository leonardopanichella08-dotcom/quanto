// Dati dimostrativi (bando Transizione 5.0). I parametri CCNL/bando sono illustrativi, non ufficiali.
export const SEED_REQUEST = {
  project_id: 'PRJ-2026-NEXUS-T50',
  grant_rules: {
    bando_id: 'TRANSIZIONE-5.0-2026',
    bando_name: 'Piano Transizione 5.0 - Efficienza Energetica & Digitalizzazione',
    max_hourly_rate_personnel: 35.0,
    max_consulting_percentage: 0.2,
    max_overhead_percentage: 0.07,
    rule_version_hash: 'a8f3b129c9e840134012480a2',
  },
  cost_items: [
    { item_id: 'LINE-001', description: 'Project Manager Junior (Integrazione IoT)', category: 'PERSONNEL', source_c_ref: 'DOC-PAYROLL-2026-08',
      ccnl_code: 'TERZO_SETTORE', employee_level: '3', ral_eur: 38000.0, fte_allocation: 0.5, duration_months: 12 },
    { item_id: 'LINE-002', description: 'Senior Software Architect (Cloud Edge)', category: 'PERSONNEL', source_c_ref: 'DOC-PAYROLL-2026-09',
      ccnl_code: 'METALMECCANICA', employee_level: '5', ral_eur: 58000.0, fte_allocation: 0.8, duration_months: 12 },
    { item_id: 'LINE-003', description: 'Consulenza specialistica Energy Audit', category: 'CONSULTING', source_c_ref: 'DOC-FACT-2026-104',
      amount_eur: 30000.0 },
  ],
}

export const SEED_PATTERN = { personnel_pct: 0.58, assets_pct: 0.12, consulting_pct: 0.25, overhead_pct: 0.05 }

export const SEED_ALLOCATION = {
  fiscal_year: 2027,
  de_minimis_residual_eur: 60000,
  historical_expenses: [
    { item_id: 'EXP-PERS', category: 'PERSONNEL', amount_eur: 150000 },
    { item_id: 'EXP-ASSET', category: 'CAPITAL_ASSETS', amount_eur: 120000, month: 4 },
    { item_id: 'EXP-CONS', category: 'CONSULTING', amount_eur: 40000 },
  ],
  available_funding_lines: [
    { fund_id: 'TRANSIZIONE-5.0-2026', name: 'Transizione 5.0', allowed_categories: ['CAPITAL_ASSETS'], coverage_pct: 0.62 },
    { fund_id: 'FSE-PLUS-2027', name: 'FSE+ Occupazione', allowed_categories: ['PERSONNEL', 'CONSULTING'], coverage_pct: 0.5,
      max_total_eur: 90000, category_max_share: { CONSULTING: 0.2 }, excludes: ['DE-MINIMIS-LOCALE'] },
    { fund_id: 'DE-MINIMIS-LOCALE', name: 'Contributo locale (de minimis)', allowed_categories: ['PERSONNEL', 'CONSULTING', 'CAPITAL_ASSETS'],
      coverage_pct: 0.3, de_minimis: true },
  ],
}

export const SEED_BANDO_TEXT = `Art. 5 - Spese ammissibili
Il costo orario del personale non può essere superiore a 35,00 euro/ora.
Le consulenze esterne non possono superare il 20% del totale del progetto.
Le spese generali forfettarie sono ammesse fino al 7% dei costi diretti.
Il contributo è pari al 60% delle spese ammissibili.
Sono ammissibili le spese sostenute dal 01/01/2026 fino al 31/12/2027.
Il CUP deve essere riportato su tutti i documenti di spesa.`
