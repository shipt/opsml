/// <reference types="vitest" />
import { defineConfig } from "vite";

export default defineConfig({
  test: {
    include: ["src/routes/*.ts"],
    environment: "jsdom",
  },
});
