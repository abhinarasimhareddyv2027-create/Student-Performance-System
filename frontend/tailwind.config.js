import forms from "@tailwindcss/forms";

/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "hsl(var(--ink))",
        panel: "hsl(var(--panel))",
        muted: "hsl(var(--muted))",
        line: "hsl(var(--line))",
        teal: "hsl(var(--teal))",
        violet: "hsl(var(--violet))",
      },
      fontFamily: {
        sans: ["DM Sans", "sans-serif"],
        display: ["Space Grotesk", "sans-serif"],
      },
      boxShadow: {
        soft: "0 18px 48px rgba(4, 10, 18, 0.16)",
      },
    },
  },
  plugins: [forms],
};