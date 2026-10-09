/** @type {import('tailwindcss').Config} */
export default {
  // relative: i glob si risolvono rispetto a questo file, non alla cwd del processo.
  content: { relative: true, files: ['./index.html', './src/**/*.{js,jsx}'] },
  theme: {
    extend: {
      colors: {
        // Accento neutro (inchiostro): selezioni e riempimenti restano sobri. Il giallo del marchio vive solo nel logo e nell'indicatore del menu.
        brand: { DEFAULT: '#1a1a17', light: '#f1f1ec', ink: '#1a1a17' },
        page: '#f6f6f3',
        ink: { DEFAULT: '#1a1a17', 2: '#4a4a43' },
        mute: '#74746a',
        line: { DEFAULT: 'rgba(26,26,23,0.10)', strong: 'rgba(26,26,23,0.20)' },
        field: '#f6f6f3',
        tint: { DEFAULT: 'rgba(26,26,23,0.035)', 2: 'rgba(26,26,23,0.07)' },
      },
      // spigoli piccoli e coerenti: niente aspetto «a bolla»
      borderRadius: { DEFAULT: '4px', md: '6px', lg: '8px', xl: '10px', '2xl': '12px', '3xl': '14px' },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', '-apple-system', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],            // cifre in colonna, stesso carattere
        code: ['JetBrains Mono', 'ui-monospace', 'monospace'],                  // solo impronte e codici
        display: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      boxShadow: { glass: '0 1px 2px rgba(26,26,23,0.04)' },
    },
  },
  plugins: [],
}
