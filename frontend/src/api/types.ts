import type { components } from './openapi_gen';

type Schemas = components['schemas'];

export type DocumentIngestRequest = Schemas['DocumentIngestRequest'];
export type DocumentIngestResponse = Schemas['DocumentIngestResponse'];
/** The ask body the UI sends (AC-3b): the schema marks every defaulted field as required. */
export type AskRequest = Pick<Schemas['QuestionRequest'], 'question' | 'strategy' | 'k_results'>;
export type Strategy = Schemas['QuestionRequest']['strategy'];
export type QuestionAnswerResponse = Schemas['QuestionAnswerResponse'];
export type SourceDocument = Schemas['SourceDocument'];
