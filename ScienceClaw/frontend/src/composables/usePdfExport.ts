import { ref } from 'vue';
import type { Ref } from 'vue';
import { exportMessagePdf } from '../api/agent';
import { showErrorToast, showSuccessToast } from '../utils/toast';

type PdfLocale = 'zh' | 'en';
type Translate = (key: string) => string;

const MAX_PDF_EXPORT_PAYLOAD_BYTES = 50 * 1024 * 1024;

const PDF_EXPORT_CODE_TO_KEY: Record<string, string> = {
  PDF_EXPORT_ACCESS_DENIED: 'pdf_export.access_denied',
  PDF_EXPORT_SESSION_NOT_FOUND: 'pdf_export.session_not_found',
  PDF_EXPORT_PAYLOAD_TOO_LARGE: 'pdf_export.payload_too_large',
  PDF_EXPORT_RENDER_FAILED: 'pdf_export.render_failed',
  PDF_EXPORT_INVALID_PDF: 'pdf_export.invalid_pdf',
  PDF_EXPORT_TIMEOUT: 'pdf_export.timeout',
  PDF_EXPORT_UNKNOWN_ERROR: 'pdf_export.unknown_error',
};

const PDF_RELEVANT_RULE_PATTERNS = [
  '.markdown-content',
  '.katex',
  '.hljs',
  '.mermaid',
  'pre',
  'code',
  'table',
  'img',
  'svg',
  '.code-block',
];

export const PDF_EXPORT_TEST_ONLY = {
  MAX_PDF_EXPORT_PAYLOAD_BYTES,
  PDF_EXPORT_CODE_TO_KEY,
};

const textEncoder = new TextEncoder();

function utf8Size(value: string): number {
  return textEncoder.encode(value).length;
}

function isRelevantCssRule(ruleText: string): boolean {
  const lowerRule = ruleText.toLowerCase();
  if (lowerRule.includes('.dark')) return false;
  return PDF_RELEVANT_RULE_PATTERNS.some((pattern) => lowerRule.includes(pattern));
}

function collectNestedRules(rule: CSSRule): string[] {
  const nested = (rule as CSSGroupingRule).cssRules;
  if (!nested) return [];

  const rules = Array.from(nested).flatMap((childRule) => collectCssRuleText(childRule));
  if (!rules.length) return [];

  if (typeof CSSMediaRule !== 'undefined' && rule instanceof CSSMediaRule) {
    return [`@media ${rule.conditionText} {\n${rules.join('\n')}\n}`];
  }

  if (typeof CSSSupportsRule !== 'undefined' && rule instanceof CSSSupportsRule) {
    return [`@supports ${rule.conditionText} {\n${rules.join('\n')}\n}`];
  }

  return rules;
}

function collectCssRuleText(rule: CSSRule): string[] {
  if (typeof CSSStyleRule !== 'undefined' && rule instanceof CSSStyleRule) {
    return isRelevantCssRule(rule.cssText) ? [rule.cssText] : [];
  }
  return collectNestedRules(rule);
}

export function collectLightPrintCss(): string {
  const collected: string[] = [];

  Array.from(document.styleSheets).forEach((styleSheet) => {
    let rules: CSSRuleList;
    try {
      rules = styleSheet.cssRules;
    } catch {
      return;
    }

    Array.from(rules).forEach((rule) => {
      collected.push(...collectCssRuleText(rule));
    });
  });

  collected.push(`
body,
.markdown-content,
.pdf-export-root {
  background: #ffffff !important;
  color: #111827 !important;
}

.markdown-content pre,
.markdown-content code,
.markdown-content .code-block-wrapper {
  background: #f3f4f6 !important;
  color: #111827 !important;
}

.markdown-content table {
  border-collapse: collapse;
}

.markdown-content table,
.markdown-content th,
.markdown-content td {
  border-color: #d1d5db !important;
}

.markdown-content img,
.markdown-content svg {
  max-width: 100%;
  height: auto;
}

.markdown-content pre,
.markdown-content table,
.markdown-content img,
.markdown-content svg {
  break-inside: avoid;
  page-break-inside: avoid;
}
`);

  return collected.join('\n');
}

export async function extractPdfErrorCode(error: unknown): Promise<string | null> {
  const responseData = (error as { details?: unknown; response?: { data?: unknown } })?.response?.data
    ?? (error as { details?: unknown })?.details;

  if (responseData instanceof Blob) {
    try {
      const parsed = JSON.parse(await responseData.text()) as { code?: unknown };
      return typeof parsed.code === 'string' ? parsed.code : null;
    } catch {
      return null;
    }
  }

  if (responseData && typeof responseData === 'object') {
    const code = (responseData as { code?: unknown }).code;
    return typeof code === 'string' ? code : null;
  }

  const code = (error as { code?: unknown })?.code;
  return typeof code === 'string' ? code : null;
}

export function mapPdfExportErrorKey(code: string | null): string {
  if (!code) return 'pdf_export.unknown_error';
  return PDF_EXPORT_CODE_TO_KEY[code] ?? 'pdf_export.unknown_error';
}

function downloadBlob(sessionId: string, blob: Blob): void {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = `scienceclaw-${sessionId}-${Date.now()}.pdf`;
  anchor.style.display = 'none';
  document.body.appendChild(anchor);
  try {
    anchor.click();
  } finally {
    anchor.remove();
    URL.revokeObjectURL(url);
  }
}

export function usePdfExport(t: Translate, exportingRef?: Ref<boolean>) {
  const exporting = exportingRef ?? ref(false);

  const exportPdf = async (
    sessionId: string,
    markdownEl: HTMLElement,
    locale: string,
  ): Promise<void> => {
    if (exporting.value) return;

    const normalizedLocale: PdfLocale = locale === 'zh' ? 'zh' : 'en';
    const html = markdownEl.innerHTML;
    const css = collectLightPrintCss();

    if (utf8Size(html) + utf8Size(css) > MAX_PDF_EXPORT_PAYLOAD_BYTES) {
      showErrorToast(t('pdf_export.payload_too_large'));
      return;
    }

    exporting.value = true;
    try {
      const blob = await exportMessagePdf(sessionId, {
        html,
        css,
        locale: normalizedLocale,
      });
      downloadBlob(sessionId, blob);
      showSuccessToast(t('pdf_export.success'));
    } catch (error) {
      const code = await extractPdfErrorCode(error);
      showErrorToast(t(mapPdfExportErrorKey(code)));
    } finally {
      exporting.value = false;
    }
  };

  return {
    exporting,
    exportPdf,
  };
}
