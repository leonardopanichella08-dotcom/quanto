import { fileURLToPath } from 'node:url'

// Percorso assoluto: Tailwind risolve la config dalla cwd, che può non essere la cartella del frontend.
const tailwindConfig = fileURLToPath(new URL('./tailwind.config.js', import.meta.url))

export default { plugins: { tailwindcss: { config: tailwindConfig }, autoprefixer: {} } }
