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
