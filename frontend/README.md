# Frontend

Vite + React 19 + TypeScript web UI for rag-docs: upload a PDF, then ask questions about it.
The UI is in Spanish; code, file names and URL hashes (`#upload`, `#ask`) are English.

## Commands

Run from `frontend/` after `npm ci`.

| Command | What it does |
|---|---|
| `npm run dev` | Dev server on `:5173` with an API proxy (below) |
| `npm run build` | `tsc -b` + `vite build` into `dist/` |
| `npm run lint` | `biome check --error-on-warnings .` (lint, format, import order) |
| `npm run format` | `biome check --write .` |
| `npm run typecheck` | `tsc -b` |
| `npm test` | vitest + Testing Library (jsdom) |
| `npm run gen:api` | Regenerate `src/api/openapi_gen.ts` from `../backend/openapi.json` |
| `npm run check:api` | Fail if `openapi_gen.ts` is not what the snapshot generates |

The gate is `check:api`, `lint`, `typecheck`, `test`, `build`, each separately.

### Dev proxy

The browser calls the API same-origin under `/api`; there is no backend host in the bundle.
`vite.config.ts` mirrors the two nginx routes: `/api/v1/*` is forwarded unchanged and
`/api/health` becomes `/health`. The target is `http://localhost:8106`; override it with
`API_PROXY_TARGET` (not `VITE_`-prefixed, so it never reaches the bundle), for example after
`kubectl port-forward svc/rag-docs-backend 8106:8106`.

## Structure

```
src/
  main.tsx  app.tsx  index.css
  styles/tokens.css        design tokens (the only place for raw colours and sizes)
  api/client.ts            typed client; fetch injectable, timeouts via AbortController
  api/errors.ts            ApiError and the fixed Spanish error copy
  api/openapi_gen.ts       generated, never hand-edited
  api/types.ts             aliases over the generated schemas
  components/              <name>.tsx + .module.css + .test.tsx
  validation.ts            title and PDF checks, base64
  test/                    setup and helpers
```

Session state (suggested titles, per-title chat threads) lives in `app.tsx` memory only. Nothing is
written to `localStorage`, `sessionStorage` or IndexedDB.

## Types (contract)

Request and response types come from the backend's OpenAPI schema, never by hand.
`backend/openapi.json` is a snapshot committed by the backend; `src/api/openapi_gen.ts` is
generated from it by `openapi-typescript` and committed. `src/api/types.ts` only aliases
`components['schemas'][...]`.

After a backend model change:

1. In `backend/`: `uv run python export_openapi.py`.
2. In `frontend/`: `npm run gen:api`, then `npm run typecheck`. Fix any drift it reports.
3. Commit the model change, `backend/openapi.json` and `src/api/openapi_gen.ts` together.

`npm run check:api` regenerates in memory and compares with the committed file. Exit 0: equal.
Exit 1: stale, or the snapshot or the file is missing. It never writes. The generated file is never
edited by hand and is excluded from Biome. Generation is not part of `build`, `test` or the Docker
build (the image context is `frontend/`, which has no `../backend`).

TypeScript is pinned to `6.0.3` because TypeScript 7 ships no JS compiler API and
`openapi-typescript` 7.13.0 crashes on it. That package also declares a peer range of
`typescript@^5`, so `package.json` has `"overrides": { "openapi-typescript": { "typescript": "$typescript" } }`;
without it `npm install` fails with ERESOLVE.

## API assumptions

- `POST /api/v1/documents` returns 201 `created` or 200 `updated` (same title again); never 409.
  The response has no chunk count.
- `POST /api/v1/documents/{title}/ask`: the document id is the title, encoded with
  `encodeURIComponent`. Titles containing `/`, or equal to `.` or `..`, cannot be routed, so the UI
  rejects them. The body is exactly `{question, strategy, k_results: 4}`.
- `/ask` sources carry no score, so none is shown. `rerank` returns no sources. `answer` may be
  `null`; `source_documents` may be absent. `pagina` is 0-based and shown as "Página N".
- `GET /api/health` (proxied to `/health`) is read for its HTTP status only.
- Timeouts: health 5 s, ingest 300 s, ask 180 s. Errors map to fixed Spanish copy; the backend
  `detail` goes to `console.error` only.
- Limits: PDF at most 20 MiB and starting with `%PDF-`; title at most 1000 characters.

## Dependencies

Runtime: `react`, `react-dom` only. Dev dependencies, each with its reason:

- `typescript` (6.0.3, exact): type checking; version constraint above.
- `openapi-typescript` (7.13.0, exact): generates the API types.
- `@biomejs/biome` (2.5.15, exact): the only linter and formatter. Pinned because the rules in
  `biome.jsonc` were verified against this version (`preset: "recommended"` replaces the
  deprecated `recommended` flag in 2.5).
- `vite`, `@vitejs/plugin-react`: dev server and bundler.
- `vitest`, `jsdom`, `@testing-library/react`, `@testing-library/dom`,
  `@testing-library/user-event`: unit and component tests.
- `@types/react`, `@types/react-dom`, `@types/node`: types (`node` for `vite.config.ts`).

## Style choices

Code follows the Google TypeScript Style Guide, enforced by Biome where it can be; the rest
(function declarations, `?` over `| undefined`, `as T` only when unavoidable, JSDoc) is review.
Where the guide is silent or conflicts with a tool, Biome's config wins:

- **Line width 100.** The guide sets no column limit; this matches the backend's ruff.
- **JSX attributes use double quotes**, the HTML/React convention; the guide covers string literals.
- **snake_case wire fields** are allowed only in `src/api/**` and tests, against the guide's
  `lowerCamelCase`. A mapping layer would double the type surface for three endpoints.
  Components read wire fields by member access and never declare snake_case names.
- **`vite.config.ts` default-exports**, because Vite requires it.
- **`import styles from './x.module.css'`** is a default import, which the guide does not forbid.
- **`src/api/openapi_gen.ts` is excluded from Biome**: tool output with its own style.
- **`biome-ignore` comments** (each with a reason): `!important` in `index.css` for `[hidden]` and
  reduced motion (the design system mandates both), index keys for static source lists, and the
  scroll-on-new-turn effect's dependencies.
