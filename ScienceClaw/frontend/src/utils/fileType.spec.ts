import { describe, expect, it, vi } from 'vitest';

vi.mock('../components/icons/FileIcon.vue', () => ({ default: { name: 'FileIcon' } }));
vi.mock('../components/icons/CodeFileIcon.vue', () => ({ default: { name: 'CodeFileIcon' } }));
vi.mock('../components/icons/PdfFileIcon.vue', () => ({ default: { name: 'PdfFileIcon' } }));
vi.mock('../components/icons/ImageFileIcon.vue', () => ({ default: { name: 'ImageFileIcon' } }));
vi.mock('../components/icons/ExcelFileIcon.vue', () => ({ default: { name: 'ExcelFileIcon' } }));
vi.mock('../components/icons/DocFileIcon.vue', () => ({ default: { name: 'DocFileIcon' } }));
vi.mock('../components/icons/MarkdownFileIcon.vue', () => ({ default: { name: 'MarkdownFileIcon' } }));
vi.mock('../components/icons/ArchiveFileIcon.vue', () => ({ default: { name: 'ArchiveFileIcon' } }));
vi.mock('../components/icons/VideoFileIcon.vue', () => ({ default: { name: 'VideoFileIcon' } }));
vi.mock('../components/icons/AudioFileIcon.vue', () => ({ default: { name: 'AudioFileIcon' } }));
vi.mock('../components/icons/PptFileIcon.vue', () => ({ default: { name: 'PptFileIcon' } }));
vi.mock('../components/filePreviews/UnknownFilePreview.vue', () => ({ default: { name: 'UnknownFilePreview' } }));
vi.mock('../components/filePreviews/MarkdownFilePreview.vue', () => ({ default: { name: 'MarkdownFilePreview' } }));
vi.mock('../components/filePreviews/CodeFilePreview.vue', () => ({ default: { name: 'CodeFilePreview' } }));
vi.mock('../components/filePreviews/ImageFilePreview.vue', () => ({ default: { name: 'ImageFilePreview' } }));
vi.mock('../components/filePreviews/MoleculeFilePreview.vue', () => ({ default: { name: 'MoleculeFilePreview' } }));
vi.mock('../components/filePreviews/ExcelFilePreview.vue', () => ({ default: { name: 'ExcelFilePreview' } }));
vi.mock('../components/filePreviews/PdfFilePreview.vue', () => ({ default: { name: 'PdfFilePreview' } }));
vi.mock('../components/filePreviews/DocxFilePreview.vue', () => ({ default: { name: 'DocxFilePreview' } }));

import { formatFileSize, getFileType } from './fileType';

describe('getFileType', () => {
  it('maps known extensions case-insensitively', () => {
    expect(getFileType('notes.MD').preview.name).toBe('MarkdownFilePreview');
    expect(getFileType('script.ts').icon.name).toBe('CodeFileIcon');
    expect(getFileType('diagram.PNG').icon.name).toBe('ImageFileIcon');
  });

  it('falls back for unknown or missing filenames', () => {
    expect(getFileType('archive.unknown').icon.name).toBe('FileIcon');
    expect(getFileType('').preview.name).toBe('UnknownFilePreview');
  });
});

describe('formatFileSize', () => {
  it('formats bytes into binary units', () => {
    expect(formatFileSize(0)).toBe('0 B');
    expect(formatFileSize(1024)).toBe('1 KB');
    expect(formatFileSize(1536, 2)).toBe('1.5 KB');
    expect(formatFileSize(1024 * 1024 * 2.5)).toBe('2.5 MB');
  });

  it('treats negative decimals as zero decimals', () => {
    expect(formatFileSize(1536, -1)).toBe('2 KB');
  });
});
