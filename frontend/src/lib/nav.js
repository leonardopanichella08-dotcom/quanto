import { createContext, useContext } from 'react'

// Permette ai componenti di aprire un'altra scheda (ed eventualmente una sezione) senza passare prop ovunque.
export const NavContext = createContext({ go: () => {} })
export const useNav = () => useContext(NavContext)

// Torna in cima alla pagina: la finestra, oppure lo schermo ridotto dell'assistente quando è aperto.
export const scrollTop = () => {
  window.scrollTo({ top: 0 })
  document.getElementById('app-scroll')?.scrollTo({ top: 0 })
}
