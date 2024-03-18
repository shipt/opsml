/** @type {import('tailwindcss').Config} */

const config = {
  content: ['./src/**/*.{html,js,svelte,ts}'],
  
  
  darkMode: 'class',

  theme: {
    extend: {
      colors: {
        primary: {
          50: '#5e0fb7',
          100: '#5e0fb7',
          200: '#5e0fb7',
          300: '#5e0fb7',
          400: '#5e0fb7',
          500: '#5e0fb7',
          600: '#5e0fb7',
          700: '#5e0fb7',
          800: '#5e0fb7',
          900: '#5e0fb7',
          },
        }
      },
    },
  };
  
  module.exports = config;