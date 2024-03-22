// @ts-check
import { join } from "path";

import { skeleton } from "@skeletonlabs/tw-plugin";
import { opsmlTheme } from "./opsml-theme";

/** @type {import('tailwindcss').Config} */

const config = {
  content: [
    "./src/**/*.{html,js,svelte,ts}",
    join(
      require.resolve("@skeletonlabs/skeleton"),
      "../**/*.{html,js,svelte,ts}"
    ),
  ],

  darkMode: "class",

  theme: {
    extend: {},
  },
  plugins: [
    skeleton({
      themes: { custom: [opsmlTheme] },
    }),
  ],
};

module.exports = config;