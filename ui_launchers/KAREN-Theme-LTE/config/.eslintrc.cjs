module.exports = {
  root: true,
  env: { browser: true, es2020: true },
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'next/core-web-vitals'
  ],
  ignorePatterns: [
    'dist',
    '.eslintrc.cjs',
    '**/__tests__/**',
    '**/*.test.ts',
    '**/*.test.tsx',
    '**/*.spec.ts',
    '**/*.spec.tsx',
  ],
  parser: '@typescript-eslint/parser',
  plugins: ['react-refresh'],
  rules: {
    'react-refresh/only-export-components': [
      'warn',
      { allowConstantExport: true },
    ],
    '@typescript-eslint/no-explicit-any': 'warn',
    '@typescript-eslint/no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],
    'react/no-unescaped-entities': 'warn',
    'react/no-children-prop': 'warn',
    'react/display-name': 'warn',
    'no-constant-condition': 'warn',
    'no-extra-semi': 'warn',
    '@next/next/no-assign-module-variable': 'warn',
    'import/no-anonymous-default-export': 'warn',
    'jsx-a11y/alt-text': 'warn',
    '@next/next/no-img-element': 'warn',
    'jsx-a11y/role-supports-aria-props': 'warn',
  },
}
