import { MAX_PDF_BYTES } from './api/client';

export const MAX_TITLE_LENGTH = 1000;

const PDF_MAGIC = '%PDF-';
const BASE64_CHUNK = 0x8000;

export const COPY_TITLE_EMPTY = 'Escribe un título.';
export const COPY_TITLE_FORBIDDEN = 'El título no puede contener «/» ni ser «.» o «..».';
export const COPY_TITLE_LONG = 'El título admite como máximo 1000 caracteres.';
export const COPY_NOT_PDF = 'El archivo no es un PDF.';
export const COPY_TOO_BIG = 'El PDF supera el límite de 20 MB.';

/** Returns the error copy for a document title, or null when it is valid. */
export function validateTitle(title: string): string | null {
  const trimmed = title.trim();
  if (trimmed === '') {
    return COPY_TITLE_EMPTY;
  }
  if (trimmed.length > MAX_TITLE_LENGTH) {
    return COPY_TITLE_LONG;
  }
  if (trimmed.includes('/') || trimmed === '.' || trimmed === '..') {
    return COPY_TITLE_FORBIDDEN;
  }
  return null;
}

function readBytes(blob: Blob): Promise<ArrayBuffer> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as ArrayBuffer);
    reader.onerror = () => reject(reader.error ?? new Error('Could not read the file'));
    reader.readAsArrayBuffer(blob);
  });
}

/** Returns the error copy for a PDF file (size, then `%PDF-` magic bytes), or null when valid. */
export async function validatePdf(file: File): Promise<string | null> {
  if (file.size > MAX_PDF_BYTES) {
    return COPY_TOO_BIG;
  }
  const head = new Uint8Array(await readBytes(file.slice(0, PDF_MAGIC.length)));
  const magic = String.fromCharCode(...head);
  return magic === PDF_MAGIC ? null : COPY_NOT_PDF;
}

/** Base64 of the file's bytes, built in chunks to avoid call-stack limits. */
export async function fileToBase64(file: File): Promise<string> {
  const bytes = new Uint8Array(await readBytes(file));
  let binary = '';
  for (let i = 0; i < bytes.length; i += BASE64_CHUNK) {
    binary += String.fromCharCode(...bytes.subarray(i, i + BASE64_CHUNK));
  }
  return btoa(binary);
}

/** Human-readable size, e.g. "1.4 MB". */
export function formatBytes(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(0)} KB`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
