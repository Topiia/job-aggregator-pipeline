/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        theme: {
          bg: "var(--theme-bg)",
          surface: "var(--theme-surface)",
          text: "var(--theme-text)",
          muted: "var(--theme-muted)",
          glow1: "var(--theme-glow1)",
          glow2: "var(--theme-glow2)",
          glow3: "var(--theme-glow3)",
        }
      }
    },
  },
  plugins: [],
}
