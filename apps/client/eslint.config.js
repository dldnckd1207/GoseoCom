import js from '@eslint/js';
import importPlugin from 'eslint-plugin-import';
import reactPlugin from 'eslint-plugin-react';
import reactHooks from 'eslint-plugin-react-hooks';
import reactRefresh from 'eslint-plugin-react-refresh';
import globals from 'globals';
import tseslint from 'typescript-eslint';

export default tseslint.config(
    { ignores: ['build', '.react-router', 'node_modules'] },

    // 전역 규칙
    {
        files: ['**/*.{ts,tsx}'],
        extends: [
            js.configs.recommended,
            ...tseslint.configs.recommended,
            reactPlugin.configs.flat.recommended,
            reactPlugin.configs.flat['jsx-runtime'],
        ],
        languageOptions: {
            ecmaVersion: 'latest',
            sourceType: 'module',
            globals: { ...globals.browser, ...globals.node },
            parserOptions: { ecmaFeatures: { jsx: true } },
        },
        settings: {
            react: { version: 'detect' },
            'import/resolver': {
                typescript: { project: './tsconfig.json' },
                node: true,
            },
        },
        plugins: {
            'react-hooks': reactHooks,
            'react-refresh': reactRefresh,
            import: importPlugin,
        },
        rules: {
            ...reactHooks.configs.recommended.rules,

            '@typescript-eslint/no-explicit-any': 'warn',
            '@typescript-eslint/no-unused-vars': [
                'error',
                { argsIgnorePattern: '^_', varsIgnorePattern: '^_' },
            ],
            '@typescript-eslint/consistent-type-imports': ['warn', { prefer: 'type-imports' }],

            'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],
            'prefer-const': 'error',
            'no-var': 'error',
            'no-console': ['warn', { allow: ['warn', 'error'] }],

            // import 순서 자동 정렬
            'import/order': [
                'error',
                {
                    groups: [
                        'builtin',
                        'external',
                        'internal',
                        ['parent', 'sibling'],
                        'index',
                        'type',
                    ],
                    pathGroups: [
                        { pattern: 'react', group: 'builtin', position: 'before' },
                        { pattern: 'react-*', group: 'builtin', position: 'before' },
                        { pattern: '~/widgets/**', group: 'internal', position: 'before' },
                        { pattern: '~/features/**', group: 'internal' },
                        { pattern: '~/entities/**', group: 'internal' },
                        { pattern: '~/shared/**', group: 'internal', position: 'after' },
                    ],
                    pathGroupsExcludedImportTypes: ['type'],
                    'newlines-between': 'always',
                    alphabetize: { order: 'asc', caseInsensitive: true },
                },
            ],
            'import/no-default-export': 'error',
            'import/consistent-type-specifier-style': ['error', 'prefer-top-level'],
        },
    },

    // features/ 내부: features 간 Hook/UI/Component 직접 import 금지 (entities/shared 경유)
    {
        files: ['app/features/**/*.{ts,tsx}'],
        rules: {
            'no-restricted-imports': [
                'error',
                {
                    patterns: [
                        {
                            group: [
                                '~/features/*/hooks',
                                '~/features/*/hooks/*',
                                '~/features/*/ui',
                                '~/features/*/ui/*',
                                '~/features/*/components',
                                '~/features/*/components/*',
                            ],
                            message: 'features 간 Hook/UI 직접 import 금지. types만 허용 (entities/shared 경유).',
                        },
                    ],
                },
            ],
        },
    },

    // routes/ 파일: default export 허용 + non-component export 허용 (loader/action/meta/links)
    {
        files: ['app/routes/**/*.{ts,tsx}', 'app/root.tsx', 'app/routes.ts'],
        rules: {
            'import/no-default-export': 'off',
            'react-refresh/only-export-components': 'off',
        },
    },

    // 설정 파일: default export 허용
    {
        files: ['*.config.{js,ts,cjs,mjs}'],
        rules: { 'import/no-default-export': 'off' },
    },
);
