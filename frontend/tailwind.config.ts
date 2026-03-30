import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0f172a",
        mist: "#eef2ff",
        panel: "#ffffff",
        accent: "#0f766e",
        warning: "#b45309",
        danger: "#b91c1c",
      },
      fontFamily: {
        sans: ['"IBM Plex Sans"', '"Avenir Next"', '"Segoe UI"', "sans-serif"],
        display: ['"Space Grotesk"', '"IBM Plex Sans"', '"Avenir Next"', "sans-serif"],
        mono: ['"IBM Plex Mono"', '"SFMono-Regular"', "monospace"],
      },
      boxShadow: {
        panel: "0 18px 50px rgba(15, 23, 42, 0.08)",
      },
      backgroundImage: {
        "hero-wash":
          "radial-gradient(circle at top left, rgba(15,118,110,0.18), transparent 38%), radial-gradient(circle at top right, rgba(180,83,9,0.16), transparent 36%)",
      },
    },
  },
  plugins: [],
} satisfies Config;
