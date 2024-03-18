/// <reference types="vitest" />
import { defineConfig } from "vite";

export default defineConfig({
  test: {
    include: ["src/lib/scripts/*.test.ts"],
    environment: "jsdom",
  },
});
