/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        navy: {
          950: '#050811',
          900: '#070B14',
          850: '#0B1120',
          800: '#0D1527',
          700: '#14203B',
          600: '#1E2F54',
        },
        cyan: {
          400: '#22d3ee',
          500: '#06b6d4',
          600: '#0891b2',
        },
        accent: {
          purple: '#8b5cf6',
          indigo: '#6366f1',
          cyan: '#06b6d4',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['Fira Code', 'Courier New', 'monospace'],
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'navy-gradient': 'linear-gradient(135deg, #070B14 0%, #0B1120 50%, #141B2D 100%)',
        'glow-gradient': 'linear-gradient(90deg, #06b6d4 0%, #8b5cf6 50%, #ec4899 100%)',
      }
    },
  },
  plugins: [],
}
