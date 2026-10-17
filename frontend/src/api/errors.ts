export type ApiErrorKind = 'http' | 'timeout' | 'network';

interface ApiErrorOptions {
  status?: number;
  detail?: string;
}

/** A failed API call. `detail` is for logs only and is never rendered. */
export class ApiError extends Error {
  readonly kind: ApiErrorKind;
  readonly status?: number;
  readonly detail?: string;

  constructor(kind: ApiErrorKind, options: ApiErrorOptions = {}) {
    super(`API ${kind} error${options.status == null ? '' : ` (${options.status})`}`);
    this.name = 'ApiError';
    this.kind = kind;
    this.status = options.status;
    this.detail = options.detail;
  }
}

const COPY_BAD_INPUT = 'Revisa los datos e inténtalo de nuevo.';
const COPY_NOT_FOUND = 'Documento no encontrado. Revisa el título o súbelo primero.';
const COPY_TOO_LARGE = 'El archivo es demasiado grande para subirlo.';
const COPY_SLOW = 'El servidor tardó demasiado en responder. Inténtalo de nuevo.';
const COPY_UNAVAILABLE = 'El servidor no pudo responder. Inténtalo de nuevo.';

/** Fixed Spanish copy for an error. Backend messages are never shown. */
export function errorMessage(error: unknown): string {
  if (!(error instanceof ApiError)) {
    return COPY_UNAVAILABLE;
  }
  if (error.kind === 'timeout') {
    return COPY_SLOW;
  }
  switch (error.status) {
    case 400:
    case 422:
      return COPY_BAD_INPUT;
    case 404:
      return COPY_NOT_FOUND;
    case 413:
      return COPY_TOO_LARGE;
    case 504:
      return COPY_SLOW;
    default:
      return COPY_UNAVAILABLE;
  }
}

/** True when trying the same request again can help (the server, not the input, failed). */
export function isRetryable(error: unknown): boolean {
  if (!(error instanceof ApiError)) {
    return true;
  }
  if (error.kind !== 'http') {
    return true;
  }
  return error.status == null || error.status >= 500;
}
