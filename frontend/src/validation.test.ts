import { describe, expect, it } from 'vitest';
import { MAX_PDF_BYTES } from './api/client';
import { pdfFile } from './test/helpers';
import { fileToBase64, formatBytes, validatePdf, validateTitle } from './validation';

describe('validateTitle', () => {
  it.each([
    ['', 'Escribe un título.'],
    ['   ', 'Escribe un título.'],
    ['a/b', 'El título no puede contener «/» ni ser «.» o «..».'],
    ['.', 'El título no puede contener «/» ni ser «.» o «..».'],
    ['..', 'El título no puede contener «/» ni ser «.» o «..».'],
    ['a'.repeat(1001), 'El título admite como máximo 1000 caracteres.'],
  ])('rejects %j', (title, expected) => {
    expect(validateTitle(title)).toBe(expected);
  });

  it('accepts 1000 characters and trims before measuring', () => {
    expect(validateTitle('a'.repeat(1000))).toBeNull();
    expect(validateTitle(`  ${'a'.repeat(1000)}  `)).toBeNull();
    expect(validateTitle('Manual de uso')).toBeNull();
  });
});

describe('validatePdf', () => {
  it('rejects a file without the magic bytes', async () => {
    const file = new File(['hello world'], 'x.pdf');
    expect(await validatePdf(file)).toBe('El archivo no es un PDF.');
  });

  it('rejects a file over the limit and accepts one at the limit', async () => {
    expect(await validatePdf(pdfFile('big.pdf', MAX_PDF_BYTES + 1))).toBe(
      'El PDF supera el límite de 20 MB.',
    );
    expect(await validatePdf(pdfFile('max.pdf', MAX_PDF_BYTES))).toBeNull();
  });
});

describe('fileToBase64', () => {
  it('encodes the bytes', async () => {
    expect(await fileToBase64(new File(['ABC'], 'a.pdf'))).toBe('QUJD');
  });
});

describe('formatBytes', () => {
  it('formats B, KB and MB', () => {
    expect(formatBytes(10)).toBe('10 B');
    expect(formatBytes(2048)).toBe('2 KB');
    expect(formatBytes(3 * 1024 * 1024)).toBe('3.0 MB');
  });
});
