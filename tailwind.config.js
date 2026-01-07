/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          orange: '#FDA052',
          purple: '#B96AF7',
          blue: '#3077F3',
          cyan: '#41E6F8',
        },
        primary: {
          50: '#EFF5FF',
          100: '#E3EDFF',
          200: '#BFD6FF',
          300: '#94BAFD',
          400: '#3077F3',
          500: '#1E50A8',
          600: '#193F85',
          700: '#11397E',
        },
        neutral: {
          50: '#F5F5F5',
          100: '#EAEAEC',
          150: '#E5E5E5',
          200: '#D5D6D9',
          300: '#C0C1C6',
          400: '#ABADB3',
          500: '#9698A0',
          600: '#82838D',
          700: '#6D6F7A',
          800: '#585A67',
          900: '#434654',
          950: '#2E3141',
        },
        success: {
          50: '#ECFDF5',
          100: '#D1FAE5',
          500: '#10B981',
          600: '#059669',
          700: '#047857',
        },
        warning: {
          50: '#FFFBEB',
          100: '#FEF3C7',
          500: '#F59E0B',
          600: '#D97706',
          700: '#B45309',
        },
        error: {
          50: '#FEF2F2',
          100: '#FEE2E2',
          500: '#EF4444',
          600: '#DC2626',
          700: '#B91C1C',
        },
      },
      fontFamily: {
        sans: ['Satoshi', 'system-ui', '-apple-system', 'sans-serif'],
      },
      fontSize: {
        'xs': ['0.75rem', { lineHeight: '1rem' }],
        'sm': ['0.875rem', { lineHeight: '1.25rem' }],
        'base': ['0.9375rem', { lineHeight: '1.5rem' }],
        'lg': ['1.0625rem', { lineHeight: '1.625rem' }],
        'xl': ['1.1875rem', { lineHeight: '1.75rem' }],
        '2xl': ['1.375rem', { lineHeight: '1.875rem' }],
        '3xl': ['1.625rem', { lineHeight: '2rem' }],
      },
    },
  },
  plugins: [],
}
