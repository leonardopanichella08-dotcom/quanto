/** @type {import('tailwindcss').Config} */
export default {
  // relative: i glob si risolvono rispetto a questo file, non alla cwd del processo.
  content: { relative: true, files: ['./index.html', './src/**/*.{js,jsx}'] },
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        brand: { DEFAULT: '#deffac', bright: '#a8fd00', dark: '#3b5d00' },
        // superfici piatte e bordi sottili: meno contrasto tra livelli, testo secondario più leggibile
        neutral: { 500: '#8c8c8c', 600: '#6a6a6a', 700: '#333333', 800: '#212121', 900: '#121212', 950: '#0a0a0a' },
      },
      borderRadius: { lg: '0.375rem', xl: '0.5rem', '2xl': '0.625rem' },
      fontFamily: {
        sans: ['Plus Jakarta Sans', 'Manrope', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
}
