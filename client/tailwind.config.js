/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{js,jsx,ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // Primary palette — indigo/blue for police/intelligence UI
        primary: {
          50:  '#eef2ff',
          100: '#e0e7ff',
          200: '#c7d2fe',
          300: '#a5b4fc',
          400: '#818cf8',
          500: '#6366f1',
          600: '#4f46e5',
          700: '#4338ca',
          800: '#3730a3',
          900: '#312e81',
          950: '#1e1b4b',
        },
        // Accent palette — red/orange for critical alerts
        alert: {
          critical: '#ef4444',
          high:     '#f97316',
          medium:   '#eab308',
          low:      '#22c55e',
        },
        // Dark UI surface colours
        surface: {
          900: '#0a0f1e',
          800: '#0f172a',
          700: '#1e293b',
          600: '#334155',
          500: '#475569',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
        kannada: ['Noto Sans Kannada', 'sans-serif'],
      },
      animation: {
        'pulse-fast': 'pulse 0.8s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'flash':      'flash 0.5s ease-in-out 3',
        'slide-in':   'slideIn 0.3s ease-out',
        'fade-in':    'fadeIn 0.4s ease-in',
      },
      keyframes: {
        flash: {
          '0%, 100%': { opacity: 1 },
          '50%':       { opacity: 0.3 },
        },
        slideIn: {
          from: { transform: 'translateX(100%)', opacity: 0 },
          to:   { transform: 'translateX(0)',    opacity: 1 },
        },
        fadeIn: {
          from: { opacity: 0, transform: 'translateY(8px)' },
          to:   { opacity: 1, transform: 'translateY(0)' },
        },
      },
      boxShadow: {
        'glow-indigo': '0 0 20px rgba(99, 102, 241, 0.35)',
        'glow-red':    '0 0 20px rgba(239, 68, 68, 0.35)',
        'glow-orange': '0 0 20px rgba(249, 115, 22, 0.35)',
      },
    },
  },
  plugins: [],
}
