import globals from "globals";
import pluginJs from "@eslint/js";
import tseslint from "typescript-eslint";
import pluginReactRecommended from "eslint-plugin-react/configs/recommended.js";
import pluginReactJsxRuntime from "eslint-plugin-react/configs/jsx-runtime.js";
import pluginJsxA11Y from "eslint-plugin-jsx-a11y/lib/configs/flat-config-base.js";
import jsxA11Y from "eslint-plugin-jsx-a11y";
import { fixupConfigRules, fixupPluginRules } from "@eslint/compat";
import eslintConfigPrettier from "eslint-config-prettier";

export default [
  { ignores: ["!**/.server", "!**/.client", "**/build"] },
  { files: ["**/*.{js,mjs,cjs,ts,jsx,tsx}"] },
  {
    plugins: { "jsx-a11y": fixupPluginRules(jsxA11Y) },
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      parserOptions: { ecmaFeatures: { jsx: true } },
    },
  },
  { languageOptions: { globals: globals.browser } },
  {
    settings: {
      react: { version: "detect" },
      formComponents: ["Form"],
      linkComponents: [
        { name: "Link", linkAttribute: "to" },
        { name: "NavLink", linkAttribute: "to" },
      ],
    },
  },
  pluginJs.configs.recommended,
  ...tseslint.configs.recommended,
  ...fixupConfigRules(pluginReactRecommended),
  ...fixupConfigRules(pluginReactJsxRuntime),
  ...fixupConfigRules(pluginJsxA11Y),
  {
    files: ["**/.eslintrc.cjs"],
    languageOptions: { globals: { ...globals.node } },
  },
  eslintConfigPrettier
];
