import js from "@eslint/js";
import globals from "globals";
import tseslint from "typescript-eslint";

export default [
  {
    ignores: [
      "**/.venv/**",
      "**/node_modules/**", 
      "**/dist/**",
      "**/build/**",
      "**/coverage/**",
      "**/.pytest_cache/**",
      "**/__pycache__/**",
      "**/serena/**"
    ]
  },
  {
    files: ["**/*.{js,mjs,cjs,ts,mts,cts}"],
    ...js.configs.recommended,
    languageOptions: { 
      globals: { ...globals.browser, ...globals.node },
      ecmaVersion: 2022,
      sourceType: "module"
    },
  },
  { 
    files: ["**/*.js"], 
    languageOptions: { sourceType: "commonjs" } 
  },
  ...tseslint.configs.recommended,
];
