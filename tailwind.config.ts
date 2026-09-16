import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        ink: "#1C1B19",
        mist: "#F4F1EA",
        paper: "#FFFcf7",
        pine: {
          DEFAULT: "#1F4A45",
          deep: "#163834",
          soft: "#2F6B64",
        },
        gold: {
          DEFAULT: "#B8956A",
          soft: "#E8D9C4",
          pale: "#F3EBE0",
        },
        sage: "#6E8470",
        clay: "#8A8175",
      },
      fontFamily: {
        sans: ["var(--font-sans)", "sans-serif"],
        serif: ["var(--font-serif)", "serif"],
      },
      boxShadow: {
        card: "0 10px 30px -18px rgba(28, 27, 25, 0.28)",
        lift: "0 18px 40px -24px rgba(22, 56, 52, 0.35)",
      },
      maxWidth: {
        content: "1120px",
      },
    },
  },
  plugins: [],
};

export default config;
