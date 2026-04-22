/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        ogma: {
          bg:       '#07040f',
          surface:  '#0d0820',
          surface2: '#140f2e',
          surface3: '#1c1640',
          50:  '#f5f3ff',
          100: '#ede9fe',
          200: '#ddd6fe',
          300: '#c4b5fd',
          400: '#a78bfa',
          500: '#8b5cf6',
          600: '#7c3aed',
          700: '#6d28d9',
          800: '#5b21b6',
          900: '#4c1d95',
          accent:    '#e879f9',
          'accent-dk': '#d946ef',
          text:      '#f5f0ff',
          secondary: '#c4b5fd',
          muted:     '#7c6fa8',
          disabled:  '#4a4065',
          success:   '#10b981',
          warning:   '#f59e0b',
          error:     '#ef4444',
          info:      '#3b82f6',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        'glow-sm': '0 0 16px rgba(124,58,237,0.35)',
        'glow':    '0 0 32px rgba(124,58,237,0.45), 0 0 64px rgba(124,58,237,0.15)',
        'glow-lg': '0 0 48px rgba(124,58,237,0.5), 0 0 96px rgba(124,58,237,0.2)',
        'accent':  '0 0 24px rgba(232,121,249,0.4)',
        'card':    '0 4px 16px rgba(0,0,0,0.5), inset 0 1px 0 rgba(139,92,246,0.08)',
        'card-lg': '0 8px 32px rgba(0,0,0,0.6), inset 0 1px 0 rgba(139,92,246,0.1)',
      },
      backgroundImage: {
        'gradient-primary': 'linear-gradient(135deg, #7c3aed 0%, #e879f9 100%)',
        'gradient-surface': 'linear-gradient(180deg, #0d0820 0%, #07040f 100%)',
        'gradient-hero':    'radial-gradient(ellipse 80% 60% at 50% 0%, rgba(124,58,237,0.3) 0%, transparent 70%)',
        'grid-subtle':      'linear-gradient(rgba(124,58,237,0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(124,58,237,0.05) 1px, transparent 1px)',
      },
      backgroundSize: {
        grid: '48px 48px',
      },
      animation: {
        'float':      'float 6s ease-in-out infinite',
        'float-slow': 'float 9s ease-in-out infinite',
        'glow-pulse': 'glowPulse 3s ease-in-out infinite',
        'shimmer':    'shimmer 2.5s linear infinite',
        'slide-up':   'slideUp 0.4s cubic-bezier(0,0,0.2,1)',
        'fade-in':    'fadeIn 0.3s ease-out',
        'scale-in':   'scaleIn 0.25s cubic-bezier(0.34,1.56,0.64,1)',
        'spin-slow':  'spin 12s linear infinite',
      },
      keyframes: {
        float: {
          '0%,100%': { transform: 'translateY(0px) rotate(0deg)' },
          '33%':     { transform: 'translateY(-16px) rotate(2deg)' },
          '66%':     { transform: 'translateY(-8px) rotate(-1deg)' },
        },
        glowPulse: {
          '0%,100%': { opacity: '0.6', transform: 'scale(1)' },
          '50%':     { opacity: '1',   transform: 'scale(1.06)' },
        },
        shimmer: {
          '0%':   { backgroundPosition: '-200% center' },
          '100%': { backgroundPosition: '200% center' },
        },
        slideUp: {
          from: { opacity: '0', transform: 'translateY(16px)' },
          to:   { opacity: '1', transform: 'translateY(0)' },
        },
        fadeIn: {
          from: { opacity: '0' },
          to:   { opacity: '1' },
        },
        scaleIn: {
          from: { opacity: '0', transform: 'scale(0.9)' },
          to:   { opacity: '1', transform: 'scale(1)' },
        },
      },
      transitionTimingFunction: {
        spring: 'cubic-bezier(0.34, 1.56, 0.64, 1)',
      },
      borderRadius: {
        '4xl': '2rem',
        '5xl': '2.5rem',
      },
      backdropBlur: {
        '2xl': '40px',
        '3xl': '64px',
      },
      screens: {
        xs: '480px',
      },
    },
  },
  plugins: [],
}
