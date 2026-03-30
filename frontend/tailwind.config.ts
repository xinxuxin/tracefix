import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0f172a",
        mist: "#eef4ff",
        panel: "#ffffff",
        line: "#e2e8f0",
        accent: "#0891b2",
        signal: "#4f46e5",
        success: "#059669",
        warning: "#d97706",
        danger: "#dc2626",
      },
      fontFamily: {
        sans: ['"IBM Plex Sans"', '"Avenir Next"', '"Segoe UI"', "sans-serif"],
        display: ['"Space Grotesk"', '"IBM Plex Sans"', '"Avenir Next"', "sans-serif"],
        mono: ['"IBM Plex Mono"', '"SFMono-Regular"', "monospace"],
      },
      boxShadow: {
        panel: "0 20px 48px rgba(15, 23, 42, 0.08)",
      },
      backgroundImage: {
        "hero-ink":
          "radial-gradient(circle at top left, rgba(34,211,238,0.18), transparent 34%), radial-gradient(circle at top right, rgba(99,102,241,0.18), transparent 30%)",
      },
    },
  },
  plugins: [],
} satisfies Config;
