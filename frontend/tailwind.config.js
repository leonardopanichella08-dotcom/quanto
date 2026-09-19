/** @type {import('tailwindcss').Config} */
export default {
  // relative: i glob si risolvono rispetto a questo file, non alla cwd del processo.
  content: { relative: true, files: ['./index.html', './src/**/*.{js,jsx}'] },
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        brand: { DEFAULT: '#deffac', bright: '#a8fd00', dark: '#3b5d00' },
      },
      fontFamily: {
        sans: ['Plus Jakarta Sans', 'Manrope', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
}
