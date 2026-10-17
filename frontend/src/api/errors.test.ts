import { describe, expect, it } from 'vitest';
import { ApiError, errorMessage, isRetryable } from './errors';

const BAD_INPUT = 'Revisa los datos e inténtalo de nuevo.';
const SLOW = 'El servidor tardó demasiado en responder. Inténtalo de nuevo.';
const UNAVAILABLE = 'El servidor no pudo responder. Inténtalo de nuevo.';

describe('errorMessage', () => {
  it.each([
    [new ApiError('http', { status: 400 }), BAD_INPUT],
    [new ApiError('http', { status: 422 }), BAD_INPUT],
    [
      new ApiError('http', { status: 404 }),
      'Documento no encontrado. Revisa el título o súbelo primero.',
    ],
    [new ApiError('http', { status: 413 }), 'El archivo es demasiado grande para subirlo.'],
    [new ApiError('http', { status: 500 }), UNAVAILABLE],
    [new ApiError('http', { status: 504 }), SLOW],
    [new ApiError('timeout'), SLOW],
    [new ApiError('network'), UNAVAILABLE],
    [new Error('unexpected'), UNAVAILABLE],
  ])('maps %o', (error, expected) => {
    expect(errorMessage(error)).toBe(expected);
  });

  it('never includes the backend detail', () => {
    const error = new ApiError('http', { status: 500, detail: 'Traceback: secret' });
    expect(errorMessage(error)).not.toContain('secret');
  });
});

describe('isRetryable', () => {
  it('retries server and transport failures, not input errors', () => {
    expect(isRetryable(new ApiError('timeout'))).toBe(true);
    expect(isRetryable(new ApiError('network'))).toBe(true);
    expect(isRetryable(new ApiError('http', { status: 502 }))).toBe(true);
    expect(isRetryable(new ApiError('http', { status: 422 }))).toBe(false);
    expect(isRetryable(new ApiError('http', { status: 404 }))).toBe(false);
  });
});
