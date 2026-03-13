import type { Config } from "tailwindcss";

export default {
  darkMode: "class",
  content: [
    './src/**/*.{js,ts,jsx,tsx}',
    './src/components/**/*.{js,ts,jsx,tsx}',
    './src/app/**/*.{js,ts,jsx,tsx}',
    './public/**/*.html',
  ],
  // Minimize safelist - only keep truly dynamic classes
  safelist: [
    // Status colors that are dynamically generated
    {
      pattern: /(text|bg|border)-(green|red|blue|yellow)-(50|200|500)/,
      variants: ['hover', 'focus', 'dark'],
    },
    // Theme-related classes that might be generated dynamically
    {
      pattern: /(density)-(compact|comfortable|spacious)/,
    },
    // Animation classes for performance optimizations
    {
      pattern: /(animate)-(fade|slide|scale|pulse)-in/,
    },
    // Karen-specific classes
    {
      pattern: /karen-(.+)/,
    },
  ],
  // Enable JIT mode optimizations
  mode: 'jit',
  // Future flags for better performance
  future: {
    hoverOnlyWhenSupported: true,
  },
  theme: {
    extend: {
      // Use CSS custom properties from our unified theme system
      fontFamily: {
        sans: ['var(--font-sans)', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
        mono: ['var(--font-mono)', 'SF Mono', 'Monaco', 'Cascadia Code', 'Roboto Mono', 'monospace'],
      },
      // Use unified color system from design tokens
      colors: {
        // Base theme colors from CSS custom properties
        background: 'hsl(var(--color-background))',
        foreground: 'hsl(var(--color-text))',
        card: {
          DEFAULT: 'hsl(var(--color-surface))',
          foreground: 'hsl(var(--color-text))'
        },
        popover: {
          DEFAULT: 'hsl(var(--color-surface))',
          foreground: 'hsl(var(--color-text))'
        },
        primary: {
          DEFAULT: 'hsl(var(--color-primary))',
          foreground: 'hsl(var(--color-background))',
          // Add semantic color variants
          50: 'hsl(var(--color-primary-50))',
          100: 'hsl(var(--color-primary-100))',
          500: 'hsl(var(--color-primary))',
          600: 'hsl(var(--color-primary-600))',
          900: 'hsl(var(--color-primary-900))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--color-secondary))',
          foreground: 'hsl(var(--color-text))'
        },
        muted: {
          DEFAULT: 'hsl(var(--color-text-secondary))',
          foreground: 'hsl(var(--color-text))'
        },
        accent: {
          DEFAULT: 'hsl(var(--color-accent))',
          foreground: 'hsl(var(--color-background))'
        },
        destructive: {
          DEFAULT: 'hsl(var(--color-error))',
          foreground: 'hsl(var(--color-background))'
        },
        // Semantic colors
        success: 'hsl(var(--color-success))',
        warning: 'hsl(var(--color-warning))',
        error: 'hsl(var(--color-error))',
        info: 'hsl(var(--color-info))',
        border: 'hsl(var(--color-border))',
        input: 'hsl(var(--color-border))',
        ring: 'hsl(var(--color-primary))',
        // Chart colors
        chart: {
          '1': 'hsl(var(--color-primary))',
          '2': 'hsl(var(--color-secondary))',
          '3': 'hsl(var(--color-accent))',
          '4': 'hsl(var(--color-warning))',
          '5': 'hsl(var(--color-error))'
        },
        sidebar: {
          DEFAULT: 'hsl(var(--color-surface))',
          foreground: 'hsl(var(--color-text))',
          primary: 'hsl(var(--color-primary))',
          'primary-foreground': 'hsl(var(--color-background))',
          accent: 'hsl(var(--color-accent))',
          'accent-foreground': 'hsl(var(--color-background))',
          border: 'hsl(var(--color-border))',
          ring: 'hsl(var(--color-primary))'
        }
      },
      // Use unified spacing system
      spacing: {
        '3xs': 'var(--space-3xs)',
        '2xs': 'var(--space-2xs)',
        'xs': 'var(--space-xs)',
        'sm': 'var(--space-sm)',
        'md': 'var(--space-md)',
        'lg': 'var(--space-lg)',
        'xl': 'var(--space-xl)',
        '2xl': 'var(--space-2xl)',
        '3xl': 'var(--space-3xl)',
        '4xl': 'var(--space-4xl)',
        '5xl': 'var(--space-5xl)',
        '6xl': 'var(--space-6xl)',
      },
      // Use unified typography system
      fontSize: {
        'xs': 'var(--text-xs)',
        'sm': 'var(--text-sm)',
        'base': 'var(--text-base)',
        'lg': 'var(--text-lg)',
        'xl': 'var(--text-xl)',
        '2xl': 'var(--text-2xl)',
        '3xl': 'var(--text-3xl)',
        '4xl': 'var(--text-4xl)',
        '5xl': 'var(--text-5xl)',
      },
      fontWeight: {
        'light': 'var(--font-weight-light)',
        'normal': 'var(--font-weight-normal)',
        'medium': 'var(--font-weight-medium)',
        'semibold': 'var(--font-weight-semibold)',
        'bold': 'var(--font-weight-bold)',
        'extrabold': 'var(--font-weight-extrabold)',
      },
      lineHeight: {
        'tight': 'var(--line-height-tight)',
        'snug': 'var(--line-height-snug)',
        'normal': 'var(--line-height-normal)',
        'relaxed': 'var(--line-height-relaxed)',
        'loose': 'var(--line-height-loose)',
      },
      // Use unified border radius system
      borderRadius: {
        'none': 'var(--radius-none)',
        'xs': 'var(--radius-xs)',
        'sm': 'var(--radius-sm)',
        'md': 'var(--radius-md)',
        'lg': 'var(--radius-lg)',
        'xl': 'var(--radius-xl)',
        '2xl': 'var(--radius-2xl)',
        '3xl': 'var(--radius-3xl)',
        'full': 'var(--radius-full)',
      },
      // Use unified shadow system
      boxShadow: {
        'xs': 'var(--shadow-xs)',
        'sm': 'var(--shadow-sm)',
        'md': 'var(--shadow-md)',
        'lg': 'var(--shadow-lg)',
        'xl': 'var(--shadow-xl)',
        '2xl': 'var(--shadow-2xl)',
        'inner': 'var(--shadow-inner)',
      },
      // Enhanced animations for better UX
      keyframes: {
        'accordion-down': {
          from: {
            height: '0'
          },
          to: {
            height: 'var(--radix-accordion-content-height)'
          }
        },
        'accordion-up': {
          from: {
            height: 'var(--radix-accordion-content-height)'
          },
          to: {
            height: '0'
          }
        },
        'karen-bounce': {
          '0%, 100%': {
            transform: 'translateY(0)',
            animationTimingFunction: 'cubic-bezier(0.8, 0, 1, 1)'
          },
          '50%': {
            transform: 'translateY(-5px)',
            animationTimingFunction: 'cubic-bezier(0, 0, 0.2, 1)'
          }
        },
        'karen-pulse': {
          '0%, 100%': {
            opacity: '1'
          },
          '50%': {
            opacity: '0.8'
          }
        },
        'karen-slide-in': {
          '0%': {
            transform: 'translateX(100%)',
            opacity: '0'
          },
          '100%': {
            transform: 'translateX(0)',
            opacity: '1'
          }
        },
        'karen-slide-out': {
          '0%': {
            transform: 'translateX(0)',
            opacity: '1'
          },
          '100%': {
            transform: 'translateX(100%)',
            opacity: '0'
          }
        },
        'karen-fade-in': {
          '0%': {
            opacity: '0',
            transform: 'scale(0.95)'
          },
          '100%': {
            opacity: '1',
            transform: 'scale(1)'
          }
        },
        'karen-progress': {
          '0%': {
            width: '100%'
          },
          '100%': {
            width: '0%'
          }
        },
        // Performance-optimized animations
        'fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' }
        },
        'slide-up': {
          '0%': {
            opacity: '0',
            transform: 'translateY(10px)'
          },
          '100%': {
            opacity: '1',
            transform: 'translateY(0)'
          }
        },
        'scale-in': {
          '0%': {
            opacity: '0',
            transform: 'scale(0.95)'
          },
          '100%': {
            opacity: '1',
            transform: 'scale(1)'
          }
        },
      },
      animation: {
        'accordion-down': 'accordion-down 0.2s ease-out',
        'accordion-up': 'accordion-up 0.2s ease-out',
        'karen-bounce': 'karen-bounce 1s infinite',
        'karen-pulse': 'karen-pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'karen-slide-in': 'karen-slide-in 0.3s ease-out',
        'karen-slide-out': 'karen-slide-out 0.3s ease-in',
        'karen-fade-in': 'karen-fade-in 0.2s ease-out',
        'karen-progress': 'karen-progress var(--duration-normal, 500ms) linear',
        // Performance-optimized animations
        'fade-in': 'fade-in var(--duration-fast, 150ms) var(--ease-out, ease-out)',
        'slide-up': 'slide-up var(--duration-fast, 150ms) var(--ease-out, ease-out)',
        'scale-in': 'scale-in var(--duration-fast, 150ms) var(--ease-out, ease-out)',
      },
      // Custom utilities for Karen layout system
      maxWidth: {
        'container': 'var(--container-max-width)',
      },
      // Viewport height utilities
      height: {
        'screen-safe': '100vh',
        'screen-safe-no-header': 'calc(100vh - var(--header-height, 0px))',
      },
      // Panel viewport utilities
      'panel-viewport-height': '100vh',
      'panel-viewport-height-desktop-auto': 'auto',
    }
  },
  plugins: [require("tailwindcss-animate")],
} satisfies Config;