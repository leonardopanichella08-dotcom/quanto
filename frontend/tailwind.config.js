/** @type {import('tailwindcss').Config} */
export default {
  // relative: i glob si risolvono rispetto a questo file, non alla cwd del processo.
  content: { relative: true, files: ['./index.html', './src/**/*.{js,jsx}'] },
  theme: {
    extend: {
      colors: {
        // Marchio: due gialli (#f1e21b intenso, #fffb96 chiaro) che si fondono in gradienti liquidi.
        brand: { DEFAULT: '#f1e21b', light: '#fffb96', ink: '#5c5500' },
        // Bianco come colore principale: inchiostro caldo per il testo, mai nero puro.
        ink: { DEFAULT: '#15150f', 2: '#45453d' },
        mute: '#6c6c62',
        line: { DEFAULT: 'rgba(21,21,15,0.09)', strong: 'rgba(21,21,15,0.17)' },
        field: 'rgba(255,255,255,0.7)',
        tint: { DEFAULT: 'rgba(21,21,15,0.045)', 2: 'rgba(21,21,15,0.075)' },
      },
      borderRadius: { lg: '0.75rem', xl: '1rem', '2xl': '1.5rem', '3xl': '2rem' },
      fontFamily: {
        // "Now" è il font del marchio: se il file è installato o in public/fonts si usa quello, altrimenti Outfit (simile).
        sans: ['Now', 'Outfit', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['Now', 'Outfit', 'ui-sans-serif', 'system-ui', 'sans-serif'],   // cifre in colonna, stesso carattere
        code: ['JetBrains Mono', 'ui-monospace', 'monospace'],                 // solo impronte e codici
      },
      boxShadow: {
        glass: '0 1px 0 rgba(255,255,255,0.95) inset, 0 12px 32px -14px rgba(110,100,0,0.22), 0 2px 6px rgba(21,21,15,0.04)',
      },
    },
  },
  plugins: [],
}
