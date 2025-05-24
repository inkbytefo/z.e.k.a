import type { Config } from "tailwindcss"

const config: Config = {
  darkMode: ["class"],
  content: [
    "./pages/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./app/**/*.{ts,tsx}",
    "./src/**/*.{ts,tsx}",
    "*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      fontFamily: {
        sans: ["-apple-system", "BlinkMacSystemFont", "SF Pro Display", "SF Pro Text", "system-ui", "sans-serif"],
        mono: ["SF Mono", "Monaco", "Inconsolata", "Roboto Mono", "monospace"],
      },
      colors: {
        // Legacy Shadcn colors (kept for compatibility)
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },

        // iOS 18 Color System
        ios: {
          background: {
            primary: "var(--ios-background-primary)",
            secondary: "var(--ios-background-secondary)",
            tertiary: "var(--ios-background-tertiary)",
          },
          surface: {
            primary: "var(--ios-surface-primary)",
            secondary: "var(--ios-surface-secondary)",
            tertiary: "var(--ios-surface-tertiary)",
          },
          text: {
            primary: "var(--ios-text-primary)",
            secondary: "var(--ios-text-secondary)",
            tertiary: "var(--ios-text-tertiary)",
            quaternary: "var(--ios-text-quaternary)",
          },
          accent: {
            blue: "var(--ios-accent-blue)",
            "blue-secondary": "var(--ios-accent-blue-secondary)",
            green: "var(--ios-accent-green)",
            orange: "var(--ios-accent-orange)",
            red: "var(--ios-accent-red)",
            purple: "var(--ios-accent-purple)",
          },
        },

        // Glass effects
        glass: {
          background: "var(--glass-background)",
          "background-strong": "var(--glass-background-strong)",
          border: "var(--glass-border)",
          "border-strong": "var(--glass-border-strong)",
        },

        cyan: {
          300: "#5edfff",
          400: "#00d7ff",
          500: "#00aac4",
          600: "#0088aa",
          700: "#006680",
          800: "#004455",
          900: "#002a33",
          950: "#001a20",
        },
      },
      borderRadius: {
        // Legacy values
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",

        // iOS 18 values
        "ios-xs": "var(--radius-xs)",
        "ios-sm": "var(--radius-sm)",
        "ios-md": "var(--radius-md)",
        "ios-lg": "var(--radius-lg)",
        "ios-xl": "var(--radius-xl)",
        "ios-2xl": "var(--radius-2xl)",
      },
      spacing: {
        "ios-xs": "var(--spacing-xs)",
        "ios-sm": "var(--spacing-sm)",
        "ios-md": "var(--spacing-md)",
        "ios-lg": "var(--spacing-lg)",
        "ios-xl": "var(--spacing-xl)",
        "ios-2xl": "var(--spacing-2xl)",
        "ios-3xl": "var(--spacing-3xl)",
      },
      backdropBlur: {
        "ios": "var(--glass-blur)",
        "ios-strong": "var(--glass-blur-strong)",
      },
      boxShadow: {
        "ios-xs": "var(--shadow-xs)",
        "ios-sm": "var(--shadow-sm)",
        "ios-md": "var(--shadow-md)",
        "ios-lg": "var(--shadow-lg)",
        "ios-xl": "var(--shadow-xl)",
        "ios-2xl": "var(--shadow-2xl)",
      },
      transitionDuration: {
        "ios-fast": "var(--duration-fast)",
        "ios-normal": "var(--duration-normal)",
        "ios-slow": "var(--duration-slow)",
      },
      transitionTimingFunction: {
        "ios-out": "var(--ease-out)",
        "ios-in-out": "var(--ease-in-out)",
        "ios-spring": "var(--ease-spring)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
        "ios-fade-in": {
          from: { opacity: "0", transform: "scale(0.95)" },
          to: { opacity: "1", transform: "scale(1)" },
        },
        "ios-slide-up": {
          from: { transform: "translateY(10px)", opacity: "0" },
          to: { transform: "translateY(0)", opacity: "1" },
        },
        "ios-pulse": {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.5" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
        "ios-fade-in": "ios-fade-in 0.3s var(--ease-out)",
        "ios-slide-up": "ios-slide-up 0.3s var(--ease-out)",
        "ios-pulse": "ios-pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}

export default config
