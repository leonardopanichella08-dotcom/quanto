import { api } from './api'

/** Le agevolazioni che lo studio ha scelto di usare nell'Allocazione, salvate per ogni lavoro: [{ id, hires }] (hires nullo = quante servono ai bisogni di crescita). */
export const loadChoice = () => api.clientState('allocation_measures').then((st) => (Array.isArray(st?.value?.items) ? st.value.items : [])).catch(() => [])
export const saveChoice = (items) => api.saveClientState('allocation_measures', { items }).catch(() => {})
export const withChoice = (items, id) => (items.some((x) => x.id === id) ? items : [...items, { id, hires: null }])
export const withoutChoice = (items, id) => items.filter((x) => x.id !== id)
