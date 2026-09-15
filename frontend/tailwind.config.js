/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        cyber: {
          900: '#070b14',
          850: '#0b1120',
          800: '#0f172a',
          750: '#15213b',
          700: '#1e293b',
          600: '#334155',
          neonBlue: '#00f0ff',
          neonRed: '#ff2a5f',
          neonGreen: '#00ff88',
          neonAmber: '#ffaa00',
          neonPurple: '#a855f7',
        }
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'radar-sweep': 'radar 4s linear infinite',
      },
      keyframes: {
        radar: {
          '0%': { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(360deg)' }
        }
      }
    },
  },
  plugins: [],
}
