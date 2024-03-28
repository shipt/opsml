import { sveltekit } from "@sveltejs/kit/vite";
import { defineConfig } from "vite";
import { vitest } from "vitest";

export default defineConfig({
  plugins: [sveltekit()],
});
