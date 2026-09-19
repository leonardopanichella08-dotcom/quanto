import { createContext, useContext } from 'react'

// Permette ai componenti di aprire un'altra scheda (ed eventualmente una sezione) senza passare prop ovunque.
export const NavContext = createContext({ go: () => {} })
export const useNav = () => useContext(NavContext)
