/// <reference types="vitest" />
import { vitePlugin as remix } from "@remix-run/dev";
import { defineConfig } from "vite";
import tsconfigPaths from "vite-tsconfig-paths";
import { coverageConfigDefaults } from "vitest/config";

export default defineConfig({
  plugins: [!process.env.VITEST && remix(), tsconfigPaths()],
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: "./vitest.setup.ts",
    coverage: {
      exclude: [...coverageConfigDefaults.exclude, "build/**"],
    },
  },
});
