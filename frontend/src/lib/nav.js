import { createContext, useContext } from 'react'

// Permette ai componenti di aprire un'altra scheda (ed eventualmente una sezione) senza passare prop ovunque.
export const NavContext = createContext({ go: () => {} })
export const useNav = () => useContext(NavContext)

// Torna in cima alla pagina: la finestra, oppure lo schermo ridotto dell'assistente quando è aperto.
export const scrollTop = () => {
  window.scrollTo({ top: 0 })
  document.getElementById('app-scroll')?.scrollTo({ top: 0 })
}

// Va a un punto preciso del Profilo di un lavoro: {to: 'setup'|'azienda'|'documenti'|'letto'|'aiuti', step?, field?, fin?: {year, key}, doc?: id|'review'}.
// Funziona anche se il Profilo non è ancora stato aperto: l'indirizzo resta in attesa finché la pagina non lo prende.
let pendingProfileTarget = null
export const profileGo = (target) => { pendingProfileTarget = target; window.dispatchEvent(new CustomEvent('quanto-profile-goto')) }
export const takeProfileTarget = () => { const t = pendingProfileTarget; pendingProfileTarget = null; return t }

// Porta lo schermo su un elemento e lo evidenzia un istante, così si capisce dove si è arrivati.
export const flashTo = (id, tries = 12) => {
  const el = document.getElementById(id)
  if (!el) { if (tries > 0) setTimeout(() => flashTo(id, tries - 1), 80); return }
  el.scrollIntoView({ behavior: 'smooth', block: 'center' })
  el.classList.add('flash-target')
  setTimeout(() => el.classList.remove('flash-target'), 2200)
}
