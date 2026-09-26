// Catalogo delle voci tipiche di un budget di progetto italiano (bandi pubblici, PNRR, fondi UE).
// Ogni voce è un punto di partenza pensato per essere naturale e intuitivo da riconoscere: pre-compila la
// categoria e i campi che tipicamente la contraddistinguono (sotto-tipo, natura del bene, tipo di contratto…),
// tutti campi che il motore già usa — non introduce nessuna regola o criterio nuovo, solo etichette e valori
// di partenza sensati per gli stessi 60 controlli. L'utente resta libero di cambiare ogni campo dopo.
//
// Raggruppate per categoria, nello stesso ordine di CATEGORY_ORDER (lib/format.js).

const T = (id, category, label, hint, defaults = {}) => ({ id, category, label, hint, defaults })

export const ITEM_TEMPLATES = [
  // ------------------------------------------------------------------ PERSONALE
  T('pm', 'PERSONNEL', 'Project Manager / responsabile di progetto', 'Coordina il progetto: pianificazione, rendicontazione, rapporti con l’ente.',
    { contract_type: 'PERMANENT', employee_level: '2', ral_eur: 42000 }),
  T('researcher', 'PERSONNEL', 'Ricercatore / ricercatrice', 'Attività di ricerca e sviluppo sul progetto.',
    { contract_type: 'FIXED_TERM', employee_level: '3', ral_eur: 35000 }),
  T('developer', 'PERSONNEL', 'Sviluppatore software / analista IT', 'Progettazione e sviluppo di software o sistemi informativi.',
    { contract_type: 'PERMANENT', employee_level: '3', ral_eur: 34000 }),
  T('technician', 'PERSONNEL', 'Tecnico di laboratorio / collaudatore', 'Prove, misure, collaudi tecnici sul progetto.',
    { contract_type: 'PERMANENT', employee_level: '4', ral_eur: 28000 }),
  T('operator', 'PERSONNEL', 'Operaio specializzato', 'Lavorazione, produzione, montaggio.', { contract_type: 'PERMANENT', employee_level: '5', ral_eur: 26000 }),
  T('admin', 'PERSONNEL', 'Impiegato amministrativo', 'Segreteria, contabilità di progetto, gestione documentale.',
    { contract_type: 'PERMANENT', employee_level: '5', ral_eur: 24000 }),
  T('fixed_term', 'PERSONNEL', 'Collaboratore a tempo determinato', 'Assunto per la durata del progetto.', { contract_type: 'FIXED_TERM', employee_level: '4', ral_eur: 27000 }),
  T('occasional', 'PERSONNEL', 'Collaborazione occasionale (co.co.co / prestazione occasionale)', 'Nei limiti di reddito annuo previsti dal criterio #13.',
    { contract_type: 'OCCASIONAL', employee_level: '4', ral_eur: 6000 }),
  T('internal_trainer', 'PERSONNEL', 'Formatore/docente interno', 'Personale interno che eroga la formazione prevista dal progetto.', { contract_type: 'PERMANENT', employee_level: '3', ral_eur: 32000 }),
  T('sales', 'PERSONNEL', 'Addetto commerciale / marketing', 'Promozione e commercializzazione dei risultati di progetto.', { contract_type: 'PERMANENT', employee_level: '4', ral_eur: 28000 }),

  // ------------------------------------------------------------------ BENI STRUMENTALI
  T('machinery', 'CAPITAL_ASSETS', 'Macchinario di produzione', 'Impianti e macchinari nuovi per la produzione.', { asset_nature: 'HARDWARE', amount_eur: 40000, is_new: true }),
  T('lab_equipment', 'CAPITAL_ASSETS', 'Attrezzatura da laboratorio', 'Strumentazione per prove, analisi, ricerca.', { asset_nature: 'HARDWARE', amount_eur: 15000, is_new: true }),
  T('pc', 'CAPITAL_ASSETS', 'Personal computer / workstation', 'Postazioni di lavoro dedicate al progetto.', { asset_nature: 'HARDWARE', amount_eur: 2500, is_new: true }),
  T('server', 'CAPITAL_ASSETS', 'Server e infrastruttura di rete', 'Server, storage, apparati di rete.', { asset_nature: 'HARDWARE', amount_eur: 12000, is_new: true }),
  T('erp_license', 'CAPITAL_ASSETS', 'Licenza software gestionale', 'ERP, CRM o altro software gestionale.', { asset_nature: 'SOFTWARE', amount_eur: 8000 }),
  T('cad_license', 'CAPITAL_ASSETS', 'Licenza software di produzione (CAD/CAM/PLM)', 'Software specialistico per progettazione o produzione.', { asset_nature: 'SOFTWARE', amount_eur: 10000 }),
  T('website', 'CAPITAL_ASSETS', 'Sviluppo di sito web o piattaforma digitale', 'Realizzazione di un sito, e-commerce o applicazione.', { asset_nature: 'SERVICE', amount_eur: 12000 }),
  T('patent', 'CAPITAL_ASSETS', 'Brevetto o licenza d’uso', 'Acquisizione o deposito di un brevetto, know-how, licenza d’uso.', { asset_nature: 'IMMATERIAL', amount_eur: 15000 }),
  T('trademark', 'CAPITAL_ASSETS', 'Marchio registrato', 'Registrazione o acquisizione di un marchio.', { asset_nature: 'IMMATERIAL', amount_eur: 5000 }),
  T('solar', 'CAPITAL_ASSETS', 'Impianto fotovoltaico / efficientamento energetico', 'Impianti per la produzione o il risparmio di energia.', { asset_nature: 'HARDWARE', amount_eur: 60000, is_new: true, energy_saving_pct: 0.1 }),
  T('vehicle', 'CAPITAL_ASSETS', 'Veicolo aziendale', 'Automezzo strumentale all’attività di progetto.', { asset_nature: 'HARDWARE', amount_eur: 25000, is_new: true }),
  T('furniture', 'CAPITAL_ASSETS', 'Arredi e allestimento', 'Arredamento di uffici, laboratori o punti vendita dedicati al progetto.', { asset_nature: 'HARDWARE', amount_eur: 8000, is_new: true }),
  T('building_works', 'CAPITAL_ASSETS', 'Opere murarie / ristrutturazione', 'Lavori edili sull’immobile: spesso esclusi dal bando (criterio #16) — verifica prima.', { asset_nature: 'REAL_ESTATE', amount_eur: 50000 }),
  T('printer3d', 'CAPITAL_ASSETS', 'Stampante 3D / prototipazione', 'Attrezzatura per prototipazione rapida.', { asset_nature: 'HARDWARE', amount_eur: 9000, is_new: true }),
  T('product_cert', 'CAPITAL_ASSETS', 'Certificazione di prodotto o di processo', 'Es. marcatura CE, certificazioni di settore legate a un investimento.', { asset_nature: 'SERVICE', amount_eur: 6000 }),

  // ------------------------------------------------------------------ CONSULENZE E FORNITORI
  T('legal', 'CONSULTING', 'Consulenza legale', 'Assistenza legale sul progetto (contratti, proprietà intellettuale…).', { amount_eur: 6000 }),
  T('tax', 'CONSULTING', 'Consulenza fiscale/tributaria', 'Adempimenti fiscali connessi al progetto.', { amount_eur: 4000 }),
  T('labor', 'CONSULTING', 'Consulenza del lavoro', 'Gestione degli aspetti giuslavoristici del personale di progetto.', { amount_eur: 3000 }),
  T('engineering', 'CONSULTING', 'Progettazione tecnica / ingegneristica', 'Progettazione di impianti, prodotti o processi.', { amount_eur: 15000 }),
  T('site_management', 'CONSULTING', 'Direzione lavori', 'Direzione e supervisione di lavori/investimenti.', { amount_eur: 10000 }),
  T('feasibility', 'CONSULTING', 'Studio di fattibilità', 'Analisi preliminare di fattibilità tecnico-economica.', { amount_eur: 8000 }),
  T('grant_application', 'CONSULTING', 'Assistenza per la domanda di finanziamento', 'Supporto nella presentazione e gestione della pratica.', { amount_eur: 5000 }),
  T('digital_marketing', 'CONSULTING', 'Consulenza di comunicazione e digital marketing', 'Strategia di comunicazione, campagne, contenuti digitali.', { amount_eur: 7000, expense_subtype: 'COMMUNICATION' }),
  T('it_dev', 'CONSULTING', 'Sviluppo IT su commessa', 'Sviluppo software affidato a un fornitore esterno.', { amount_eur: 20000 }),
  T('due_diligence', 'CONSULTING', 'Due diligence', 'Verifica approfondita in vista di un’operazione straordinaria.', { amount_eur: 9000 }),
  T('mgmt_cert', 'CONSULTING', 'Certificazione di sistema di gestione (ISO)', 'Es. ISO 9001, 14001, 45001, SA8000.', { amount_eur: 6000 }),
  T('testing', 'CONSULTING', 'Collaudo e verifica tecnica indipendente', 'Test e verifiche svolte da un soggetto terzo.', { amount_eur: 4000 }),
  T('outsourced_rd', 'CONSULTING', 'Ricerca esterna (in conto terzi)', 'Attività di ricerca e sviluppo commissionata a un ente terzo.', { amount_eur: 25000 }),
  T('audit', 'CONSULTING', 'Revisione contabile indipendente', 'Certificazione del rendiconto da un revisore indipendente (criterio #39).', { amount_eur: 3000, expense_subtype: 'AUDIT' }),
  T('press', 'CONSULTING', 'Ufficio stampa e comunicazione istituzionale', 'Comunicati, rassegna stampa, relazioni con i media.', { amount_eur: 4000, expense_subtype: 'COMMUNICATION' }),

  // ------------------------------------------------------------------ SPESE GENERALI
  T('rent', 'OVERHEAD', 'Canone di locazione degli uffici', 'Affitto degli spazi usati per il progetto, in proporzione a mq e mesi (criterio #42).', { amount_eur: 12000, expense_subtype: 'RENT' }),
  T('utilities', 'OVERHEAD', 'Utenze (luce, gas, acqua, telefono)', 'Da imputare con un criterio di ripartizione oggettivo (criterio #43).', { amount_eur: 3000, expense_subtype: 'UTILITIES' }),
  T('maint_ordinary', 'OVERHEAD', 'Manutenzione ordinaria', 'Manutenzione corrente di impianti o beni: di norma non ammissibile (criterio #27).', { amount_eur: 2000, expense_subtype: 'MAINTENANCE_ORDINARY' }),
  T('maint_extra', 'OVERHEAD', 'Manutenzione straordinaria', 'Interventi di manutenzione straordinaria legati al progetto.', { amount_eur: 5000, expense_subtype: 'MAINTENANCE_EXTRAORDINARY' }),
  T('guarantee', 'OVERHEAD', 'Fideiussione bancaria o assicurativa', 'Garanzia richiesta dal bando per l’anticipo o la partecipazione (criterio #38).', { amount_eur: 2500, expense_subtype: 'GUARANTEE' }),
  T('insurance', 'OVERHEAD', 'Polizza assicurativa di progetto', 'Copertura assicurativa specifica del progetto o dei beni acquisiti.', { amount_eur: 1500 }),
  T('overhead_audit', 'OVERHEAD', 'Spese di revisione contabile', 'Certificazione del rendiconto (criterio #39).', { amount_eur: 3000, expense_subtype: 'AUDIT' }),
  T('consumables', 'OVERHEAD', 'Materiali di consumo e cancelleria', 'Materiali non capitalizzabili usati nel progetto.', { amount_eur: 1500 }),
  T('communication', 'OVERHEAD', 'Comunicazione e divulgazione del progetto', 'Materiali informativi, targhe, sito dedicato al progetto (criterio #37).', { amount_eur: 2000, expense_subtype: 'COMMUNICATION' }),
  T('financial_charges', 'OVERHEAD', 'Spese e oneri bancari/finanziari', 'Interessi, oneri del debito: quasi sempre esclusi (criterio #16).', { amount_eur: 500, expense_subtype: 'FINANCIAL_CHARGES' }),
  T('representation', 'OVERHEAD', 'Spese di rappresentanza', 'Ammissibili solo se dimostrabilmente finalizzate al progetto (criterio #44).', { amount_eur: 800, expense_subtype: 'REPRESENTATION' }),

  // ------------------------------------------------------------------ FORMAZIONE
  T('external_trainer', 'TRAINING', 'Docenza esterna', 'Compenso a formatori/docenti esterni al progetto.', { amount_eur: 4000 }),
  T('training_materials', 'TRAINING', 'Materiale didattico', 'Dispense, manuali, materiali di supporto alla formazione.', { amount_eur: 800 }),
  T('training_venue', 'TRAINING', 'Noleggio aula o location per la formazione', 'Affitto di spazi per lo svolgimento dei corsi.', { amount_eur: 1500 }),
  T('elearning', 'TRAINING', 'Piattaforma e-learning', 'Licenza o sviluppo di una piattaforma di formazione a distanza.', { amount_eur: 3000 }),
  T('skills_cert', 'TRAINING', 'Certificazione delle competenze acquisite', 'Esami o certificazioni professionali al termine del corso.', { amount_eur: 1200 }),
  T('training_lodging', 'TRAINING', 'Vitto e alloggio per la formazione residenziale', 'Spese per corsi che richiedono la presenza in sede diversa.', { amount_eur: 2000 }),
  T('language_training', 'TRAINING', 'Formazione linguistica', 'Corsi di lingua per il personale coinvolto nel progetto.', { amount_eur: 1500 }),
  T('mandatory_training', 'TRAINING', 'Formazione obbligatoria (es. sicurezza sul lavoro)', 'Aggiornamento professionale richiesto dalla normativa.', { amount_eur: 1000 }),
]

export function searchTemplates(query, category) {
  const q = (query || '').trim().toLowerCase()
  return ITEM_TEMPLATES.filter((t) => (!category || t.category === category) && (!q || t.label.toLowerCase().includes(q) || t.hint.toLowerCase().includes(q)))
}
