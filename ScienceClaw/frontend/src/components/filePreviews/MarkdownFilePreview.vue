<template>
    <div class="prose prose-slate max-w-none dark:prose-invert w-full" v-html="renderedContent"></div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import { useRoute } from 'vue-router';
import { marked } from 'marked';
import DOMPurify from 'dompurify';
import hljs from 'highlight.js/lib/core';
import bash from 'highlight.js/lib/languages/bash';
import css from 'highlight.js/lib/languages/css';
import javascript from 'highlight.js/lib/languages/javascript';
import json from 'highlight.js/lib/languages/json';
import markdown from 'highlight.js/lib/languages/markdown';
import plaintext from 'highlight.js/lib/languages/plaintext';
import python from 'highlight.js/lib/languages/python';
import typescript from 'highlight.js/lib/languages/typescript';
import xml from 'highlight.js/lib/languages/xml';
import type { FileInfo } from '../../api/file';
import { downloadFile } from '../../api/file';
import { downloadSandboxFile } from '../../api/agent';

hljs.registerLanguage('bash', bash);
hljs.registerLanguage('css', css);
hljs.registerLanguage('html', xml);
hljs.registerLanguage('javascript', javascript);
hljs.registerLanguage('js', javascript);
hljs.registerLanguage('json', json);
hljs.registerLanguage('markdown', markdown);
hljs.registerLanguage('md', markdown);
hljs.registerLanguage('plaintext', plaintext);
hljs.registerLanguage('python', python);
hljs.registerLanguage('py', python);
hljs.registerLanguage('ts', typescript);
hljs.registerLanguage('typescript', typescript);
hljs.registerLanguage('xml', xml);

const content = ref('');
const route = useRoute();

const props = defineProps<{
    file?: FileInfo;
    content?: string;
}>();

// Configure marked options
const renderer = new marked.Renderer();
renderer.code = ({ text, lang }: { text: string, lang?: string }) => {
    const validLang = !!(lang && hljs && hljs.getLanguage(lang));
    const highlighted = validLang
        ? hljs.highlight(text, { language: lang, ignoreIllegals: true }).value
        : text;
    return `<pre><code class="hljs language-${lang || 'plaintext'}">${highlighted}</code></pre>`;
};

marked.use({
    renderer,
    breaks: true,
    gfm: true
});

// Compute rendered HTML content
const renderedContent = computed(() => {
    if (!content.value) return '';
    try {
        const html = marked.parse(content.value);
        return DOMPurify.sanitize(html as string);
    } catch (error) {
        console.error('Failed to render markdown:', error);
        return `<pre class="text-sm text-red-500">Failed to render markdown content</pre>`;
    }
});

watch(() => props.content, (newVal) => {
    if (newVal) {
        content.value = newVal;
    }
}, { immediate: true });

watch(() => props.file?.file_id, async (fileId) => {
    if (!fileId) return;
    try {
        const sandboxPath = props.file?.metadata?.sandbox_path;
        let blob: Blob;
        if (sandboxPath) {
            const sessionId = (props.file?.metadata?.session_id as string)
                || (route.params.sessionId as string);
            blob = await downloadSandboxFile(sessionId, sandboxPath);
        } else {
            blob = await downloadFile(fileId);
        }
        const text = await blob.text();
        content.value = text;
    } catch (error) {
        console.error('Failed to load file content:', error);
        content.value = '(Failed to load file content)';
    }
}, { immediate: true });
</script>
