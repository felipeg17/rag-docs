import { vi } from 'vitest';
import type { ApiClient } from '../api/client';
import type { DocumentIngestResponse, QuestionAnswerResponse } from '../api/types';

/** A client whose methods are all mocks; override the ones a test cares about. */
export function fakeApi(overrides: Partial<ApiClient> = {}): ApiClient {
  return {
    health: vi.fn().mockResolvedValue(undefined),
    ingestDocument: vi.fn(),
    ask: vi.fn(),
    ...overrides,
  };
}

export function ingestResponse(
  title: string,
  status: DocumentIngestResponse['status'] = 'created',
): DocumentIngestResponse {
  return { document_id: 'id-1', title, status, message: 'ok' };
}

export function answerResponse(
  answer: string | null,
  sources: QuestionAnswerResponse['source_documents'] = [],
): QuestionAnswerResponse {
  return {
    answer,
    document_id: 'id-1',
    question: 'q',
    strategy: 'standard',
    source_documents: sources,
  };
}

/** A File whose content starts with the PDF magic bytes. */
export function pdfFile(name = 'manual.pdf', size = 64): File {
  const header = '%PDF-1.4\n';
  return new File([header, new Uint8Array(Math.max(size - header.length, 0))], name, {
    type: 'application/pdf',
  });
}
