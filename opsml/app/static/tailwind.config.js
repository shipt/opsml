/** @type {import('tailwindcss').Config} */

const config = {
  content: ["./src/**/*.{html,js,svelte,ts}"],

  darkMode: "class",

  theme: {
    extend: {
      fontFamily: {
        boing: ["Boing"],
      },
      colors: {
        primary: {
          50: "#b4a7d5",
          100: "#b4a7d5",
          200: "#b4a7d5",
          300: "#5e0fb7",
          400: "#5e0fb7",
          500: "#5e0fb7",
          600: "#5e0fb7",
          700: "#5e0fb7",
          800: "#5e0fb7",
          900: "#5e0fb7",
        },
      },
    },
  },
};

module.exports = config;
