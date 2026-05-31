import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import monacoEditorPlugin from 'vite-plugin-monaco-editor';
import { resolve } from 'path';

const monacoMultiDiffStylePath = '/monaco-editor/esm/vs/editor/browser/widget/multiDiffEditor/style.css';

function fixMonacoMultiDiffNestedCss() {
  return {
    name: 'fix-monaco-multidiff-nested-css',
    enforce: 'pre' as const,
    transform(code: string, id: string) {
      const normalizedId = id.replace(/\\/g, '/');

      if (!normalizedId.endsWith(monacoMultiDiffStylePath)) {
        return null;
      }

      return code.replace(/\n(\s*)a \{/g, '\n$1:is(a) {');
    },
  };
}

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    fixMonacoMultiDiffNestedCss(),
    (monacoEditorPlugin as any).default({})
  ],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  optimizeDeps: {
    exclude: ['lucide-vue-next'],
  },
  build: {
    chunkSizeWarningLimit: 1400,
    rollupOptions: {
      output: {
        manualChunks(id) {
          const normalizedId = id.replace(/\\/g, '/');

          if (normalizedId.includes('/node_modules/monaco-editor/')) {
            if (normalizedId.includes('/vs/basic-languages/')) return 'monaco-languages';
            if (normalizedId.includes('/vs/language/')) return 'monaco-language-services';
            if (normalizedId.includes('/vs/editor/')) return 'monaco-editor-core';
            if (normalizedId.includes('/vs/base/')) return 'monaco-base';
            return 'monaco-runtime';
          }

          if (normalizedId.includes('/node_modules/katex/')) return 'katex';
          if (normalizedId.includes('/node_modules/highlight.js/')) return 'highlight';
          if (normalizedId.includes('/node_modules/marked/')) return 'markdown';
          if (normalizedId.includes('/node_modules/dompurify/')) return 'markdown-sanitize';
        },
      },
    },
  },
  server: {
    host: true,
    port: 5173,
    proxy: {
      '/api': {
        target: process.env.BACKEND_URL || 'http://localhost:12001',
        changeOrigin: true,
        ws: true,
      },
      '/task-service': {
        target: process.env.TASK_SERVICE_URL || 'http://localhost:12002',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/task-service/, ''),
      },
    },
  },
});
