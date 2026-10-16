/** @type {import('tailwindcss').Config} */
export default {
  // relative: i glob si risolvono rispetto a questo file, non alla cwd del processo.
  content: { relative: true, files: ['./index.html', './src/**/*.{js,jsx}'] },
  theme: {
    extend: {
      colors: {
        // Chiaro, quasi bianco, con un solo inchiostro: gli accenti sono i colori di stato (verde, ambra, rosso), usati con parsimonia.
        brand: { DEFAULT: '#1d1d1f', light: '#f5f5f7', ink: '#1d1d1f' },
        page: '#f5f5f7',
        ink: { DEFAULT: '#1d1d1f', 2: '#515154' },
        mute: '#86868b',
        line: { DEFAULT: 'rgba(0,0,0,0.06)', strong: 'rgba(0,0,0,0.12)' },
        field: '#f5f5f7',
        tint: { DEFAULT: 'rgba(0,0,0,0.04)', 2: 'rgba(0,0,0,0.07)' },
      },
      // raggi generosi: superfici morbide, niente spigoli da cruscotto
      borderRadius: { DEFAULT: '8px', md: '10px', lg: '12px', xl: '16px', '2xl': '20px', '3xl': '26px' },
      fontFamily: {
        sans: ['-apple-system', 'BlinkMacSystemFont', 'SF Pro Text', 'Inter', 'ui-sans-serif', 'system-ui', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['-apple-system', 'BlinkMacSystemFont', 'SF Pro Text', 'Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],      // cifre in colonna, stesso carattere
        code: ['SF Mono', 'JetBrains Mono', 'ui-monospace', 'monospace'],                                                      // solo impronte e codici
        display: ['-apple-system', 'BlinkMacSystemFont', 'SF Pro Display', 'Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      boxShadow: { glass: '0 1px 2px rgba(0,0,0,0.04), 0 12px 32px -16px rgba(0,0,0,0.10)' },
    },
  },
  plugins: [],
}
