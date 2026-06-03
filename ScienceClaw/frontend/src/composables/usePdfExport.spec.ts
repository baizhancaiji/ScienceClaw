import { ref } from 'vue';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import {
  collectLightPrintCss,
  extractPdfErrorCode,
  mapPdfExportErrorKey,
  PDF_EXPORT_TEST_ONLY,
  usePdfExport,
} from './usePdfExport';
import { exportMessagePdf } from '../api/agent';
import { showErrorToast, showSuccessToast } from '../utils/toast';

vi.mock('../api/agent', () => ({
  exportMessagePdf: vi.fn(),
}));

vi.mock('../utils/toast', () => ({
  showErrorToast: vi.fn(),
  showSuccessToast: vi.fn(),
}));

const t = (key: string) => `t:${key}`;

describe('usePdfExport', () => {
  beforeEach(() => {
    vi.mocked(exportMessagePdf).mockReset();
    vi.mocked(showErrorToast).mockReset();
    vi.mocked(showSuccessToast).mockReset();
    document.head.innerHTML = '';
    document.body.innerHTML = '';
    vi.stubGlobal('URL', {
      createObjectURL: vi.fn(() => 'blob:pdf'),
      revokeObjectURL: vi.fn(),
    });
  });

  it('collects relevant light CSS and filters dark rules', () => {
    const style = document.createElement('style');
    style.textContent = `
      .markdown-content { color: #111827; }
      .dark .markdown-content { color: white; }
      .unrelated { color: red; }
      pre code { background: #f3f4f6; }
    `;
    document.head.appendChild(style);

    const css = collectLightPrintCss();

    expect(css).toContain('.markdown-content');
    expect(css).toContain('pre code');
    expect(css).toContain('background: #ffffff');
    expect(css).not.toContain('.dark');
    expect(css).not.toContain('.unrelated');
  });

  it('does not call the API when payload exceeds 50MB', async () => {
    const markdownEl = document.createElement('div');
    markdownEl.innerHTML = 'x'.repeat(PDF_EXPORT_TEST_ONLY.MAX_PDF_EXPORT_PAYLOAD_BYTES + 1);
    const pdfExport = usePdfExport(t);

    await pdfExport.exportPdf('session-1', markdownEl, 'zh');

    expect(exportMessagePdf).not.toHaveBeenCalled();
    expect(showErrorToast).toHaveBeenCalledWith('t:pdf_export.payload_too_large');
  });

  it('posts rendered html, light css, and locale without dark', async () => {
    vi.mocked(exportMessagePdf).mockResolvedValue(new Blob(['%PDF']));
    const clickSpy = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});
    const markdownEl = document.createElement('div');
    markdownEl.innerHTML = '<h1>Report</h1>';
    const pdfExport = usePdfExport(t, ref(false));

    await pdfExport.exportPdf('session-1', markdownEl, 'zh');

    expect(exportMessagePdf).toHaveBeenCalledTimes(1);
    expect(exportMessagePdf).toHaveBeenCalledWith('session-1', expect.objectContaining({
      html: '<h1>Report</h1>',
      locale: 'zh',
    }));
    const payload = vi.mocked(exportMessagePdf).mock.calls[0][1] as unknown as Record<string, unknown>;
    expect(payload).not.toHaveProperty('dark');
    expect(showSuccessToast).toHaveBeenCalledWith('t:pdf_export.success');
    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:pdf');
    clickSpy.mockRestore();
  });

  it('ignores repeat clicks while exporting', async () => {
    const markdownEl = document.createElement('div');
    markdownEl.innerHTML = '<p>Report</p>';
    const pdfExport = usePdfExport(t, ref(true));

    await pdfExport.exportPdf('session-1', markdownEl, 'en');

    expect(exportMessagePdf).not.toHaveBeenCalled();
  });

  it('maps backend error code to i18n key without raw blob text', async () => {
    const rawBlob = new Blob([
      JSON.stringify({
        code: 'PDF_EXPORT_RENDER_FAILED',
        detail: 'stderr traceback secret',
      }),
    ], { type: 'application/json' });
    vi.mocked(exportMessagePdf).mockRejectedValue({ response: { data: rawBlob } });
    const markdownEl = document.createElement('div');
    markdownEl.innerHTML = '<p>Report</p>';
    const pdfExport = usePdfExport(t);

    await pdfExport.exportPdf('session-1', markdownEl, 'en');

    expect(showErrorToast).toHaveBeenCalledWith('t:pdf_export.render_failed');
    expect(showErrorToast).not.toHaveBeenCalledWith(expect.stringContaining('stderr'));
  });

  it('extracts blob error codes and falls back for unknown codes', async () => {
    await expect(extractPdfErrorCode({
      response: { data: new Blob([JSON.stringify({ code: 'PDF_EXPORT_TIMEOUT' })]) },
    })).resolves.toBe('PDF_EXPORT_TIMEOUT');

    expect(mapPdfExportErrorKey('PDF_EXPORT_TIMEOUT')).toBe('pdf_export.timeout');
    expect(mapPdfExportErrorKey('UNEXPECTED')).toBe('pdf_export.unknown_error');
    expect(mapPdfExportErrorKey(null)).toBe('pdf_export.unknown_error');
  });
});
