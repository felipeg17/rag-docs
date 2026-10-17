import { ApiError } from './errors';
import type {
  AskRequest,
  DocumentIngestRequest,
  DocumentIngestResponse,
  QuestionAnswerResponse,
  Strategy,
} from './types';

/** Largest PDF the UI accepts: 20 MiB (shown to users as "20 MB"). */
export const MAX_PDF_BYTES = 20 * 1024 * 1024;
export const HEALTH_TIMEOUT_MS = 5_000;
export const INGEST_TIMEOUT_MS = 300_000;
export const ASK_TIMEOUT_MS = 180_000;

/** The UI always asks for the backend's default number of chunks. */
export const K_RESULTS = 4;
const DOCUMENT_TYPE = 'documento-pdf';
const MAX_DETAIL_LENGTH = 500;

export type FetchLike = (input: string, init?: RequestInit) => Promise<Response>;

export interface ApiClient {
  health(): Promise<void>;
  /** `contentBase64` is the PDF's bytes, base64-encoded. */
  ingestDocument(title: string, contentBase64: string): Promise<DocumentIngestResponse>;
  ask(documentId: string, question: string, strategy: Strategy): Promise<QuestionAnswerResponse>;
}

async function readDetail(response: Response): Promise<string> {
  try {
    const text = await response.text();
    return text.slice(0, MAX_DETAIL_LENGTH);
  } catch {
    return '';
  }
}

/**
 * Builds the API client. `fetchImpl` is injectable for tests; `baseUrl` is same-origin because
 * nginx (and the Vite dev proxy) forward `/api` to the backend.
 */
export function createApiClient(
  fetchImpl: FetchLike = (input, init) => globalThis.fetch(input, init),
  baseUrl = '/api',
): ApiClient {
  async function request(
    path: string,
    timeoutMs: number,
    init: RequestInit = {},
  ): Promise<Response> {
    const controller = new AbortController();
    let timedOut = false;
    const timer = setTimeout(() => {
      timedOut = true;
      controller.abort();
    }, timeoutMs);
    try {
      const response = await fetchImpl(`${baseUrl}${path}`, { ...init, signal: controller.signal });
      if (!response.ok) {
        const detail = await readDetail(response);
        if (response.status >= 500) {
          console.error('API error', response.status, detail);
        }
        throw new ApiError('http', { status: response.status, detail });
      }
      return response;
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      if (timedOut) {
        throw new ApiError('timeout');
      }
      console.error('API network error', error);
      throw new ApiError('network');
    } finally {
      clearTimeout(timer);
    }
  }

  async function postJson<T>(path: string, body: unknown, timeoutMs: number): Promise<T> {
    const response = await request(path, timeoutMs, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    try {
      return (await response.json()) as T;
    } catch {
      throw new ApiError('http', { status: response.status, detail: 'Invalid JSON body' });
    }
  }

  return {
    async health() {
      await request('/health', HEALTH_TIMEOUT_MS);
    },
    ingestDocument(title, contentBase64) {
      const body: DocumentIngestRequest = {
        title,
        document_type: DOCUMENT_TYPE,
        document_content: contentBase64,
      };
      return postJson<DocumentIngestResponse>('/v1/documents', body, INGEST_TIMEOUT_MS);
    },
    ask(documentId, question, strategy) {
      const body: AskRequest = { question, strategy, k_results: K_RESULTS };
      return postJson<QuestionAnswerResponse>(
        `/v1/documents/${encodeURIComponent(documentId)}/ask`,
        body,
        ASK_TIMEOUT_MS,
      );
    },
  };
}
