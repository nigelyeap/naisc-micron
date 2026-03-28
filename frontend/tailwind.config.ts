import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: ['class'],
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        'bg-base':    'var(--bg-base)',
        'bg-panel':   'var(--bg-panel)',
        'bg-raised':  'var(--bg-raised)',
        border:       'var(--border)',
        'text-primary': 'var(--text-primary)',
        'text-muted':   'var(--text-muted)',
        'accent-blue':  'var(--accent-blue)',
        'accent-red':   'var(--accent-red)',
        'accent-amber': 'var(--accent-amber)',
        'accent-green': 'var(--accent-green)',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
}

export default config
