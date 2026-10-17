import { createApiClient } from './client';

/** The default client, over `globalThis.fetch`. */
export const apiClient = createApiClient();
