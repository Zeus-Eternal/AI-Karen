import type { Config } from 'tailwindcss';

const config: Config = {
  darkMode: ['class'],
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  prefix: "",
  theme: {
    extend: {
      // TiTan's clean design tokens
      colors: {
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        card: 'hsl(var(--card))',
        'card-foreground': 'hsl(var(--card-foreground))',
        popover: 'hsl(var(--popover))',
        'popover-foreground': 'hsl(var(--popover-foreground))',
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        
        // KAREN's enhanced theme colors
        karen: {
          electric: 'hsl(var(--karen-electric))',
          charcoal: 'hsl(var(--karen-charcoal))',
          lavender: 'hsl(var(--karen-lavender))',
        }
      },
      
      // Enhanced animations from both systems
      animation: {
        'accordion-down': 'accordion-down 0.2s ease-out',
        'accordion-up': 'accordion-up 0.2s ease-out',
        'fade-in': 'fade-in 0.3s ease-out',
        'slide-up': 'slide-up 0.3s ease-out',
        'pulse-glow': 'pulse-glow 2s ease-in-out infinite',
        'karen-bounce': 'karen-bounce 1.5s ease-in-out infinite',
        'karen-pulse': 'karen-pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      
      // Enhanced spacing and typography
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
      },
      
      fontFamily: {
        sans: ['var(--font-sans)', 'sans-serif'],
        mono: ['var(--font-mono)', 'monospace'],
      },
      
      // Enhanced border radius
      borderRadius: {
        'karen': '0.75rem',
        'karen-lg': '1rem',
      },
      
      // Enhanced shadows
      boxShadow: {
        'karen': '0 4px 20px hsl(var(--karen-electric) / 0.15)',
        'karen-lg': '0 8px 40px hsl(var(--karen-electric) / 0.2)',
        'karen-glow': '0 0 20px hsl(var(--karen-electric) / 0.3)',
      },
      
      // Enhanced gradients
      backgroundImage: {
        'karen-gradient': 'linear-gradient(135deg, hsl(var(--karen-electric)) 0%, hsl(var(--karen-lavender)) 100%)',
        'karen-gradient-dark': 'linear-gradient(135deg, hsl(var(--karen-electric) / 0.9) 0%, hsl(var(--karen-lavender) / 0.9) 100%)',
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
    require('@tailwindcss/aspect-ratio'),
  ],
};

export default config;