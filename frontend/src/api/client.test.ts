import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ASK_TIMEOUT_MS, createApiClient, HEALTH_TIMEOUT_MS } from './client';
import { ApiError } from './errors';

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status });
}

function firstCall(fetchMock: ReturnType<typeof vi.fn>): [string, RequestInit] {
  return fetchMock.mock.calls[0] as [string, RequestInit];
}

beforeEach(() => {
  vi.spyOn(console, 'error').mockImplementation(() => undefined);
});

afterEach(() => {
  vi.useRealTimers();
  vi.restoreAllMocks();
});

describe('ask', () => {
  it('encodes the title in the path and sends exactly question, strategy and k_results', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse({ answer: 'x', source_documents: [] }));
    await createApiClient(fetchMock).ask('a b?#c', 'Qué es', 'rerank');
    const [url, init] = firstCall(fetchMock);
    expect(url).toBe('/api/v1/documents/a%20b%3F%23c/ask');
    expect(init.method).toBe('POST');
    expect(JSON.parse(init.body as string)).toEqual({
      question: 'Qué es',
      strategy: 'rerank',
      k_results: 4,
    });
  });
});

describe('ingestDocument', () => {
  it('sends exactly title, document_type and document_content', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(
        jsonResponse({ document_id: '1', title: 't', status: 'created', message: '' }, 201),
      );
    const result = await createApiClient(fetchMock).ingestDocument('t', 'QUJD');
    const [url, init] = firstCall(fetchMock);
    expect(url).toBe('/api/v1/documents');
    expect(JSON.parse(init.body as string)).toEqual({
      title: 't',
      document_type: 'documento-pdf',
      document_content: 'QUJD',
    });
    expect(result.status).toBe('created');
  });
});

describe('health', () => {
  it('calls /api/health', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ status: 'healthy' }));
    await createApiClient(fetchMock).health();
    expect(firstCall(fetchMock)[0]).toBe('/api/health');
  });
});

describe('errors', () => {
  it('aborts at the timeout and raises a timeout error', async () => {
    vi.useFakeTimers();
    const fetchMock = vi.fn(
      (_url: string, init?: RequestInit) =>
        new Promise<Response>((_resolve, reject) => {
          init?.signal?.addEventListener('abort', () =>
            reject(new DOMException('aborted', 'AbortError')),
          );
        }),
    );
    const pending = createApiClient(fetchMock).health();
    const assertion = expect(pending).rejects.toMatchObject({ kind: 'timeout' });
    await vi.advanceTimersByTimeAsync(HEALTH_TIMEOUT_MS);
    await assertion;
    expect(ASK_TIMEOUT_MS).toBeGreaterThan(HEALTH_TIMEOUT_MS);
  });

  it('maps a non-2xx response to an http error with the status', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response('{"detail":"boom"}', { status: 500 }));
    const error = await createApiClient(fetchMock)
      .ask('t', 'q', 'standard')
      .catch((caught: unknown) => caught);
    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ kind: 'http', status: 500 });
    expect(console.error).toHaveBeenCalled();
  });

  it('maps a rejected fetch to a network error', async () => {
    const fetchMock = vi.fn().mockRejectedValue(new TypeError('Failed to fetch'));
    await expect(createApiClient(fetchMock).health()).rejects.toMatchObject({ kind: 'network' });
  });

  it('maps an unparseable success body to an http error', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response('not json', { status: 200 }));
    await expect(createApiClient(fetchMock).ask('t', 'q', 'standard')).rejects.toMatchObject({
      kind: 'http',
      status: 200,
    });
  });
});
