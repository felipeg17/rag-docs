# SPEC-002: Replace the Streamlit frontend with a Vite + React web UI

| Field | Value |
|---|---|
| Status | Done |
| Findings | F-028, F-029 |
| Issue | — |
| Domains | backend, frontend, k8s, ci, qa, docs |
| Branch | `spec/SPEC-002-web-frontend` |
| Base | `dev` @ `1fbb820` |

## Context

The user asked for a modern, responsive and minimal frontend to replace the Streamlit app, using
`/Users/felipe/code/projects/customs-agent/web/` as the reference: Vite, React 19, TypeScript
strict, Biome 2, vitest, CSS modules, nginx-unprivileged with a same-origin `/api` proxy. The
target standards are `.claude/agents/frontend-agent.md` (rewritten for the new stack, including
the Google TypeScript Style Guide code-style rules) and `.claude/skills/design/SKILL.md`. Both are
uncommitted on `dev` and were carried over to this branch.

The reference is scaled down. rag-docs has three JSON endpoints and no SSE, so the reference's SSE
parser, state machine, tabs, history and reruns are out of scope.

### Current frontend (verified on `dev` @ `1fbb820`, 2026-10-16)

- **App**: Streamlit, with two sidebar pages, "Documento" and "Chatbot" (`frontend/front.py:12-18`).
  All UI strings are Spanish.
- **Requests run on the Streamlit server, not in the browser.**
  - `load_backend_config` builds `http://{API_HOST}:{API_PORT}/` from env (`frontend/utils/utils.py:4-9`).
  - The values come from `frontend/frontend.env.template:1-2` and `k8s/base/frontend/configmap.yaml:6-7`.
- **Ask page** ([F-028](../findings/F-028-frontend-requests.md), [F-029](../findings/F-029-frontend-ux-security.md)):
  - The title says "Chabot" (`frontend/components/chatbot.py:8`).
  - The document is picked by typing its title into a free-text field (`chatbot.py:10`).
  - The title goes into the path unencoded (`chatbot.py:15`).
  - Strategy is hard-coded to `rerank` and `k_results` to 4 (`chatbot.py:19-20`).
  - `requests.post` has no timeout and no exception handling (`chatbot.py:26`).
  - The response is dumped as key/value lines (`chatbot.py:30-31`).
  - Errors print the raw response body (`chatbot.py:33`), which includes backend internals ([F-007](../findings/F-007-error-handling-leaks-internals.md)).
- **Upload page**:
  - The title is not validated (`frontend/components/qa_pdf.py:14`).
  - There is no timeout (`qa_pdf.py:29`).
  - The response is dumped raw (`qa_pdf.py:31-36`).
- **Image**:
  - Built on `python:3.10-slim` and runs as root. It writes `/root/.streamlit/config.toml` with `enableCORS = false` and `enableXsrfProtection = false` (`frontend/Dockerfile:31-37`).
  - It exposes 8502 (`Dockerfile:39-41`).
  - `pyproject.toml:23` packages a non-existent `front` module.
- **Kubernetes**:
  - Container and Service use port 8502 (`k8s/base/frontend/deployment.yaml:22`, `service.yaml:10-11`). Skaffold forwards 8502 to 8502 (`k8s/base/frontend/skaffold.yaml:28-32`).
  - The deployment has no probes (`deployment.yaml:17-33`). This is the frontend-probes item of [F-027](../findings/F-027-k8s-resources-availability.md), which this spec addresses only in part. F-027 is deliberately not listed under *Findings*, because its Ollama-requests item stays open.
- **Compose**: the frontend service uses `network_mode: "host"` and `env_file: frontend/frontend.env` (`docker-compose.yaml:22-38`). The template sets `API_HOST=rag-docs-backend` (`frontend.env.template:1`).
- **CI**: `check-format-frontend` runs `uv sync` and `ruff format --check` in `frontend/` (`.github/workflows/submission-check.yml:70-97`). It has no frontend type-check or test job. `.github/CODEOWNERS` points at `/front/`, a path that does not exist.
- **Docs that describe the Streamlit app** (found with `grep -rnE 'streamlit|front\.py|8501|8502|frontend\.env|ruff check \.'`):
  - `README.md:16,41,85`, which gives port 8501. The deployed port is 8502.
  - `CLAUDE.md:9,49`
  - `frontend/README.md`
  - `docs/guides/setup.md:12,77-82,119-129`
  - `docs/development/contributing.md:31-36`
  - `.claude/CLAUDE.md:40`, the frontend gate baseline.
  - `resources/RESULTS.md:183`, a historical Spanish report. It is not updated (see *Non-goals*).

### Backend contract the new UI consumes (unchanged by this spec)

| Route | Facts (verified by reading the code) |
|---|---|
| `GET /health` | Lives at the root, not under `/api` (`backend/main.py:11`, `backend/app/api/routers/health.py:12`). Always returns 200 with `{"status": "healthy", "database": "connected"\|"disconnected"}` (`health.py:14-18`). |
| `POST /api/v1/documents` | Body is `DocumentIngestRequest`: `title` (no `min_length`), `document_type` (default `"documento-pdf"`) and `document_content` (base64-validated) (`backend/app/models/requests/document_request.py:7-22`). Returns **201** `created` for a new title and **200** `updated` when the title already exists in the vector store; never 409 (`backend/app/api/routers/v1/document.py:57-96`). The response is `{document_id, title, status, message}` with no chunk count (`backend/app/models/responses/document_response.py:6-12`). Bytes that are not a PDF fail in `PDFLoader` (`backend/app/services/document/pdf_loader.py:36-38`). That failure surfaces as a **500** whose `detail` carries the exception text (`document.py:100-106`), and it happens after the Postgres row is created (`document.py:50-55`). |
| `POST /api/v1/documents/{document_id}/ask` | `document_id` is the title (`document.py:193`). Body is `QuestionRequest`: `question` (`min_length=1`), `strategy` (`standard` by default, or `rerank`), `k_results` 1–10 (default 4) and `metadata_filter` (`backend/app/models/requests/search_request.py:14-22`). A title missing from the vector store returns **404** (`document.py:202-206`). `rerank` returns `source_documents: []` (`document.py:210-218`). `standard` returns sources with `score: null` (`document.py:230-237`). Each source is `{page_content, metadata, score}` (`backend/app/models/responses/qa_response.py:6-9`). `answer` is nullable (`qa_response.py:14-16`). Other failures return **500** with internals in `detail` (`document.py:264-270`). |
| `POST /api/v1/documents/{document_id}/search` | Not used by the UI (see *Non-goals*). The deployed-stack ACs use it as an LLM-free probe through the proxy. |
| Listing documents | There is no list route: `document.py` declares only the three `POST` routes above (`document.py:28,109,182`). See *Non-goals* and [F-033](../findings/F-033-no-document-list.md). |
| Chunk metadata | `pagina` is the **0-based** page index (`backend/app/services/document/text_extractor.py:30,46`). |
| Wire field names | All JSON fields are `snake_case` (`document_type`, `document_content`, `k_results`, `metadata_filter`, `document_id`, `source_documents`, `page_content`). This bears on REQ-12's naming rules. |
| CORS | `backend/main.py` adds no CORS middleware, so the browser must call the API same-origin. |
| Titles containing `/` | They cannot be reached by `/ask` or `/search`, even percent-encoded. uvicorn 0.34.0 unquotes the path before routing (`uvicorn/protocols/http/h11_impl.py:198`, `httptools_impl.py:257`), so `%2F` becomes `/`. Starlette 0.45.3 then matches `{document_id}` with `[^/]+` (`starlette/convertors.py:20-21`). Versions come from `backend/uv.lock`; the files were read from the installed packages in `backend/.venv`. Encoding the path (F-028) fixes spaces, `?`, `#` and `%`, but not `/`. Titles `.` and `..` are unreachable too. `encodeURIComponent` leaves dots alone, and WHATWG URL parsing collapses the dot segment. Executed with node v24.15.0: `new URL('/api/v1/documents/' + encodeURIComponent('..') + '/ask', 'http://x').pathname` → `/api/v1/ask`, and `'.'` → `/api/v1/documents/ask`. |

The backend's OpenAPI document can be dumped offline from the backend venv. `main.py:8` builds
the app at import. The dump exited 0 with no server, database, vector store or LLM reachable.
Executed 2026-10-16 in `backend/`:
`uv run --offline python -c "import json,sys; from main import app; sys.stdout.write(json.dumps(app.openapi(), indent=2, sort_keys=True, ensure_ascii=False)+'\n')"`.

- It exits 0 and prints OpenAPI 3.1.0 with 4 paths and 10 schemas.
- The output was byte-identical (`cmp`) across three environments: an empty environment (`env -i PATH HOME`), the `backend-unit-tests` CI job's variables (`submission-check.yml:155-161`), and `backend/backend.env.template` sourced into the shell.
- `google.api_core` prints a `FutureWarning` about Python 3.10 on stderr. stdout is unaffected.
- `/health` declares no response model, so its schema is empty. The UI reads only its HTTP status (REQ-6).

How the generated types map these models is in *Design* § API types.

### Library and runtime behavior (verified against docs, not memory)

| Component | Fact | Source |
|---|---|---|
| nginx | `client_max_body_size` defaults to `1m`. A larger body returns **413**. | nginx.org `ngx_http_core_module` |
| nginx | Sizes take `k`/`m` suffixes. The syntax page does not state whether `m` is 10⁶ or 2²⁰ bytes; `30m` covers the 20 MiB limit either way (see *Design* § Limits). | nginx.org `docs/syntax.html` (read 2026-10-16) |
| nginx | `proxy_read_timeout` and `proxy_send_timeout` default to `60s`. They apply between two successive reads/writes, not to the whole response. | nginx.org `ngx_http_proxy_module` |
| nginx | When `proxy_pass` has no URI, the request URI goes upstream **as the client sent it**, encoding included. When it has a URI, the part that matched the location is replaced. | nginx.org `ngx_http_proxy_module` |
| nginx | A literal hostname in `proxy_pass` is resolved when the configuration loads. A variable is resolved per request through `resolver`. | Inferred from `ngx_http_proxy_module` text. The load-time half was **executed** on 2026-10-16: the built image run with `API_HOST=no-such-host.invalid` logs `[emerg] host not found in upstream "no-such-host.invalid" in /etc/nginx/conf.d/default.conf:18` and nginx does not start |
| `nginxinc/nginx-unprivileged` (alpine-slim base) | `EXPOSE 8080`. The listen port is rewritten to 8080, the image runs as `USER 101`, and the PID file and temp paths are in `/tmp`. Any port above 1024 can be used by UID 101; this spec uses 8502 (open question 3). The base image's `EXPOSE 8080` is inherited: the built image's `ExposedPorts` is `{"8080/tcp":{},"8502/tcp":{}}`, while `netstat -ltn` in the running container shows a single listener, `0.0.0.0:8502` (executed 2026-10-16). That a child Dockerfile cannot remove an inherited `EXPOSE` is k8s-agent's report, not checked against Docker's docs. | `github.com/nginx/docker-nginx-unprivileged` README, `mainline/alpine-slim/Dockerfile`; executed |
| `nginxinc/nginx-unprivileged` | Ships `20-envsubst-on-templates.sh`. At start it renders `/etc/nginx/templates/*.template` into `/etc/nginx/conf.d`, substituting only environment variables that are **defined**, so nginx's own lowercase variables such as `$host` stay intact. `/etc/nginx` is group-writable for UID 101. | `mainline/alpine-slim/20-envsubst-on-templates.sh`, `alpine-slim/Dockerfile`; Docker Hub `nginx` "Using environment variables in nginx configuration" |
| Vite | `server.proxy` keys match the start of the path. `rewrite` changes the forwarded path (the docs example is `/api/bar` → `/bar`). | vite.dev `config/server-options` |
| Biome | `@biomejs/biome` `latest` is `2.5.15` (published 2026-09-30). In 2.5, `linter.rules.recommended` is deprecated in favour of `linter.rules.preset: "recommended"`. | `npm view @biomejs/biome dist-tags time`; deprecation diagnostic from `biome check` |
| Biome | Every rule REQ-12 names exists in 2.5.15 under the group shown: `suspicious/noExplicitAny`, `suspicious/noDoubleEquals` (option `ignoreNull`), `suspicious/noVar`, `suspicious/noTsIgnore` (since 2.0.0), `suspicious/noConstEnum`, `style/noNonNullAssertion`, `style/useImportType`, `style/useExportType`, `style/useConst`, `style/noDefaultExport`, `style/useDefaultSwitchClause`, `style/useThrowOnlyError`, `style/useThrowNewError`, `style/useConsistentTypeDefinitions` (since 2.1.4, option `style: "interface"`), `style/useConsistentArrayType` (option `syntax: "shorthand"`), `style/noNamespace`, `style/useFilenamingConvention`, `style/useNamingConvention`. | `biome explain <rule>` and `configuration_schema.json` from the installed 2.5.15 package |
| Biome | Several recommended rules default to severity `warn` and some style rules to `info`. `biome check` exits 0 on warnings unless `--error-on-warnings` is passed. | `biome explain` ("Default severity"); executed |
| Biome | `useFilenamingConvention` accepts camelCase, kebab-case, snake_case **or the name of an export** by default, so `UploadView.tsx` passes unless `filenameCases` is `["snake_case"]`. It checks only JS/TS file names, not `.css`. | `biome explain useFilenamingConvention`; executed |
| Biome | Executed against a fixture tree with the config in *Design* § Code style. Passed: `app.tsx`, `upload_view.tsx` exporting `function UploadView` (PascalCase component), `import styles from './upload_view.module.css'` with `styles.dropZone`, `CONSTANT_CASE` constants, `value == null`, `!` in a `.test.tsx`, snake_case wire fields in `src/api/types.ts` and in an object literal in `src/api/client.ts`, shorthand destructuring `const { page_content } = doc` in a component, `export default` in `vite.config.ts`, files under `dist/` and `package-lock.json` (excluded), an `index.html`, a `tsconfig.app.json` and `tsconfig.node.json` with `/* … */` comments, and an npm-written `package.json`. Failed with the named rule: `UploadView.tsx` (`useFilenamingConvention`), `export default` in `src/` (`noDefaultExport`), `x: any` (`noExplicitAny`), `x!.length` in `src/` (`noNonNullAssertion`), `// @ts-ignore` (`noTsIgnore`), `a == b` (`noDoubleEquals`), a `switch` without `default` (`useDefaultSwitchClause`), `type Point = { … }` (`useConsistentTypeDefinitions`), a value import used only as a type (`useImportType`), a snake_case object-literal key outside `src/api/` and tests (`useNamingConvention`), a missing semicolon and double-quoted strings (`format`). **Not** caught: `// @ts-expect-error` and `// @ts-nocheck`. | Biome 2.5.15 run in the architect's scratchpad, 2026-10-16 |
| Google TypeScript Style Guide | Rules quoted from the guide: files are `snake_case` (§ Naming → Imports); "Do not use default exports"; "Explicitly end all statements using a semicolon"; "Ordinary string literals are delimited with single quotes"; "Use optional fields … rather than a `\|undefined` type"; "Prefer function declarations over arrow functions or function expressions when defining named functions"; "Always use triple equals" (`== null` allowed); "All `switch` statements must contain a `default` statement group"; "Do not use `@ts-ignore` nor the variants `@ts-expect-error` or `@ts-nocheck`"; interfaces for object types; `T[]` for simple element types; `UpperCamelCase` for "component functions in TSX"; `lowerCamelCase` for properties. The guide sets **no column limit**: code is "autoformatted". It is silent on JSX attribute quotes and on wire-format property names. | google.github.io/styleguide/tsguide.html, fetched 2026-10-16 |
| TypeScript | `latest` is `7.0.2` (2026-07-08). Its package's `.` export is only `./lib/version.cjs`, so it ships no JS compiler API. `6.0.3` (2026-04-16) is the latest 6.x. | `npm view typescript dist-tags time exports` |
| openapi-typescript | `latest` is `7.13.0` (2026-02-11) and declares `peerDependencies: { typescript: "^5.x" }`. | `npm view openapi-typescript dist-tags time peerDependencies` |
| openapi-typescript + TypeScript | Executed in the architect's scratchpad on 2026-10-16, with node v24.15.0 and npm 11.12.1:<br>• `openapi-typescript@7.13.0` with `typescript@6.0.3` and **no** `overrides`: `npm install` fails with ERESOLVE (exit 1).<br>• The same pair with `"overrides": { "openapi-typescript": { "typescript": "$typescript" } }` installs, and `npm ls` shows a single, deduped `typescript@6.0.3`. Generating from the dump above writes a 457-line file, and `tsc` (`strict`, `noUncheckedIndexedAccess`) passes on it plus an alias module.<br>• With `typescript@7.0.2` and the override, generation fails (exit 1) with `TypeError: Cannot read properties of undefined (reading 'createKeywordTypeNode')`.<br>Reference: customs-agent/web runs TS `~6.0.2` (installed 6.0.3) with Vite 8, vitest 5 and this override (`customs-agent/web/package.json`). | Executed; `customs-agent/web/package.json` |
| openapi-typescript CLI | `--check` regenerates in memory and compares it with the `-o` file. Exit 0 when equal; exit 1 when stale (`✘ Generated types are not up-to-date!`). It also exits 1 when the input or output file is missing, so those cases share one code. It never writes in `--check` mode (`bin/cli.js` `checkStaleOutput`). Fields that have a schema `default` are generated as **required**. A `default_factory` field has no schema default, so it stays optional (`source_documents?`). | `openapi-typescript --help` and `bin/cli.js` from the 7.13.0 package; executed |
| openapi-typescript output vs Biome | The generated file uses double quotes, 4-space indent and lowercase exported interfaces (`paths`, `components`). Without an exclusion, the *Design* § Code style config reports 19 errors on it (format and `useNamingConvention`). With `"!src/api/openapi_gen.ts"` in `files.includes` it reports none. An alias module (`import type { components } from './openapi_gen'`, `type Schemas = components['schemas']`, `Pick<…>`) passes the config unchanged. | Biome 2.5.15, executed 2026-10-16 |
| Local toolchain | node v24.15.0, npm 11.12.1, Docker 29.2.1; minikube running | `node -v`, `npm -v`, `docker info`, `minikube status` (2026-10-16) |

## Goals

- Replace the Streamlit app in `frontend/` with a Vite + React 19 + TypeScript (strict) single-page app for two jobs: upload a PDF, and ask questions about a document.
- Serve the built app from nginx-unprivileged. nginx proxies the API same-origin, so the bundle never contains a backend host.
- Resolve the request-handling and UX/security problems of F-028 and F-029 that the new app can fix without backend changes.
  - F-029 is fully covered: chat UX, input validation, and the CORS/XSRF flags plus the bogus `packages` entry, both removed with Streamlit.
  - F-028 is covered for encoding, timeouts, error handling and the strategy selector. The `k` selector is out of scope by user decision (open question 7); F-028's follow-up is split accordingly, so QA's `Fixed (SPEC-002)` stays accurate.
- Hold the new code to the Google TypeScript Style Guide, enforced by Biome 2 where Biome can (REQ-12).
- Derive the frontend's API types from the backend's OpenAPI schema, so that backend drift fails CI instead of failing at runtime (REQ-14).
- Keep the change proportionate: the reference stack, minus everything rag-docs' backend cannot feed (SSE, history, reruns, tabs, attachments, models).
- Leave Kubernetes via Skaffold + minikube as the only way to run the stack. Docker Compose, the `Makefile` and `backend/backend.env.template` are removed (user decision, 2026-10-17).

## Non-goals

- Any change to backend behavior: API models, routes, status codes, `Settings`, the 500 `detail` leak (F-007), rerank sources (F-008). The only backend change is tooling for REQ-14: an export script, the committed schema snapshot and one unit test. None of them is in the image (`backend/Dockerfile:19-21` copies only `app`, `main.py` and `alembic.ini`).
- A document picker and the `GET /api/v1/documents` route it needs. Deferred to a later spec; tracked as [F-033](../findings/F-033-no-document-list.md).
- A `k_results` control. The UI always sends 4 (open question 7).
- A `/search` UI.
- Streaming answers, persisted chat history, authentication, user accounts, an i18n framework and a theme toggle.
- Playwright e2e tests and a mock mode (open question 5). AC-10's Playwright MCP browser is QA tooling, not a project dependency.
- Porting the reference's SSE parser, state machine, history, reruns, attachments or model picker.
- Ollama resource requests and PodDisruptionBudgets (the rest of F-027), and GKE (#30).
- `resources/RESULTS.md`, a historical report that is left as written.
- Any way to run the stack other than Kubernetes (Skaffold + minikube), including a replacement for Docker Compose or the `Makefile` (user decision, 2026-10-17).

## Requirements

- **REQ-1 (stack)**: `frontend/` shall contain only the new web app. Every Python file, `pyproject.toml` and `uv.lock` are removed. The app uses Vite, React 19 and TypeScript `strict` with `noUncheckedIndexedAccess`, CSS modules plus the design tokens, Biome 2 (lint, format and import order; REQ-12), and vitest with Testing Library (jsdom). The package manager is npm, and `package-lock.json` is committed. Runtime dependencies are `react` and `react-dom` only. These dev dependencies are pinned exactly (`npm i -D -E`):
  - `typescript` `6.0.3`. TypeScript 7 has no JS compiler API, and openapi-typescript crashes on it (see *Library behavior*).
  - `openapi-typescript` `7.13.0`.
  - `@biomejs/biome` `2.5.15` (see *Design* § Code style).

  `package.json` has `"overrides": { "openapi-typescript": { "typescript": "$typescript" } }`. Without it, `npm install` fails with ERESOLVE, because openapi-typescript's peer range is `^5.x`.
- **REQ-2 (upload)**: The Upload view shall let the user choose a PDF, by drop or browse, and set a title, then send `POST /api/v1/documents` with `{title, document_type: "documento-pdf", document_content: <base64>}`.
  - Before sending, the UI checks:
    - the title, trimmed, is non-empty, at most 1000 characters (`documents.title VARCHAR(1000)`, `backend/app/infrastructure/database/models.py:58`), contains no `/`, and is not `.` or `..` (see *Context*: those titles cannot be reached by `/ask`);
    - the file starts with the `%PDF-` magic bytes;
    - the file is at most `MAX_PDF_BYTES` = 20 × 1024 × 1024 bytes (20 MiB, shown to users as "20 MB").
  - If a check fails, the field shows its error from the *Design* copy table and no request is sent.
  - A 201 response shows a success that names the title and offers the Ask view for it.
  - A 200 (`status: "updated"`) shows the "already indexed" success, with the same next action.
- **REQ-3 (ask)**: The Ask view shall take a document title and a question, and send `POST /api/v1/documents/{encodeURIComponent(title.trim())}/ask` with `{question, strategy, k_results: 4}`.
  - The title field is free text. It offers, as suggestions (`<datalist>`), the titles that got a 201 or 200 from the Upload view in this page session. Suggestions live in memory only and are lost on reload.
  - Before sending, the UI checks the title with REQ-2's title rules (trimmed, non-empty, at most 1000 characters, no `/`, not `.` or `..`) and that the question, trimmed, is non-empty. If a check fails, the field shows its error from the *Design* copy table and no request is sent.
  - A secondary two-option control picks the strategy: "Estándar" (`standard`, the default) or "Rerank" (`rerank`). When Rerank is selected, a hint says it returns no sources.
  - `k_results` is always 4 (the backend default); there is no control for it.
  - Enter submits and Shift+Enter inserts a newline.
  - The answer is rendered as plain text with line breaks preserved, never as HTML. A `null` answer shows the no-answer message.
  - Each answer lists its sources: page (`pagina + 1`, as "Página N") and excerpt. `/ask` sources carry no score, so none is shown.
  - When `source_documents` is empty (always the case for `rerank`), the UI shows the no-sources note.
- **REQ-4 (chat history)**: Questions and answers shall accumulate in memory for the page session, kept per document title. The Ask view shows the thread of the title currently entered; returning to an earlier title shows its thread again. Threads survive switching to the Upload view and back, and are cleared on reload. Nothing is persisted (no `localStorage`, `sessionStorage` or IndexedDB).
- **REQ-5 (API client)**: Every HTTP call shall go through the typed client in `frontend/src/api/`.
  - The client encodes path segments, gives each request a timeout via `AbortController`, and maps non-2xx, timeout and network failures to a typed error.
  - The UI maps that error to the fixed copy in *Design*.
  - The UI never shows the backend `detail` or any raw body. For 5xx the detail goes to `console.error` only.
- **REQ-6 (backend status)**: The header shall show the backend status from `GET /api/health` as a dot plus a text label: "Comprobando…", then "Servidor en línea" (HTTP 200) or "Servidor sin conexión" (anything else, timeout or network error).
- **REQ-7 (design)**: The UI shall follow `.claude/skills/design/SKILL.md`, with the overrides in *Design*:
  - no horizontal scroll at 360, 768 or 1280 px;
  - one primary button per view;
  - idle, loading, success and error states for every request;
  - keyboard operable;
  - answers announced through `aria-live="polite"`;
  - light and dark follow the system `prefers-color-scheme`, with no toggle;
  - all UI copy is Spanish, with correct accents, and the document declares `<html lang="es">`. Code identifiers, file names and the URL hashes (`#upload`, `#ask`) stay English.
- **REQ-8 (serving)**: The image shall serve the built bundle from nginx-unprivileged as UID 101, listening on port 8502.
  - The same-origin routes are:
    - `/api/v1/*` goes to the backend with the path unchanged, as the client sent it;
    - `/api/health` goes to the backend's `/health`;
    - any other `/api/*` path returns 404 and is not proxied;
    - any other path that is not a file gets `index.html`.
  - The upstream is built from `API_HOST`/`API_PORT` when the container starts.
  - The request body limit and proxy timeouts cover the client limits and timeouts.
  - Responses carry `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer` and a `Content-Security-Policy` that allows only same-origin scripts, styles and connections, and forbids framing.
- **REQ-9 (local dev)**: `npm run dev` shall serve the UI with a Vite proxy that mirrors REQ-8's two API routes exactly. The proxy target defaults to `http://localhost:8106` and can be overridden by an environment variable that is not exposed to the bundle.
- **REQ-10 (deployment)**: `skaffold run`/`dev` with the existing profiles shall deploy the new frontend with readiness and liveness probes on a static nginx path, independent of the backend. The deploy shall stabilize. Container port, Service port and the skaffold port-forward stay 8502, so `http://localhost:8502` is unchanged.
- **REQ-11 (CI)**: On PRs touching `frontend/**` **or `backend/openapi.json`**, CI shall run these in `frontend/` on Node 24, with the npm cache keyed on `frontend/package-lock.json`: `npm ci`, `npm run check:api`, `npm run lint`, `npm run typecheck`, `npm test` and `npm run build`. The frontend job stays Node-only: no Python or uv. The Python/uv frontend jobs are removed. On PRs touching `backend/**`, the existing `backend-unit-tests` job runs the snapshot test (REQ-14) without changes.
- **REQ-12 (code style)**: Frontend code shall follow the [Google TypeScript Style Guide](https://google.github.io/styleguide/tsguide.html) as listed in `.claude/agents/frontend-agent.md` § Code style. Biome 2 is the only linter and formatter; `npm run lint` is exactly `biome check --error-on-warnings .` and enforces formatting, import order and the rules below. Concretely:
  - **File names** are `snake_case` for every source file, test and CSS module (`app.tsx`, `upload_view.tsx`, `upload_view.module.css`, `upload_view.test.tsx`). Types, interfaces and component functions are `UpperCamelCase`; functions and variables `lowerCamelCase`; module-level constants `CONSTANT_CASE`; acronyms are written as words (`apiUrl`, `pdfFile`).
  - **Exports**: named exports only. The only default export is in `vite.config.ts`, which Vite requires; the vitest configuration lives in the same file, so no other exception exists. `import type` for type-only imports.
  - **Formatting**: semicolons always, single quotes for string literals, 2-space indent, line width 100.
  - **Types**: no `any` (use `unknown` and narrow); no non-null `!` outside test files; no `@ts-ignore`, `@ts-expect-error` or `@ts-nocheck`; `interface` for object shapes and `type` for unions; `?` instead of `| undefined`; `T[]` for simple element types.
  - **Statements**: `const` by default and never `var`; `===` except `== null`; every `switch` has a `default` as its last clause; throw only `new Error(...)` or subclasses.
  - **Functions**: function declarations for named functions, arrow functions for callbacks.
  - **Wire types**: the API's `snake_case` field names are kept as-is. They come from the generated `src/api/openapi_gen.ts`, and `src/api/types.ts` aliases them (REQ-14; the guide says "Use declared interfaces to represent server-side JSON"). snake_case property names are allowed only in `src/api/**` and in test files. Components read wire fields by member access (`doc.page_content`) or shorthand destructuring; they never declare snake_case names of their own.
  - **Suppressions**: no `biome-ignore` without a written reason in the same comment.
  - The rules Biome cannot enforce (function declarations versus `const f = () => …`, `?` versus `| undefined`, `as T` only when unavoidable, JSDoc on exported symbols, `@ts-expect-error`/`@ts-nocheck`) are enforced by review, plus the grep in AC-15 for the last one.
- **REQ-13 (docs)**: No document in scope shall describe the Streamlit frontend, port 8501 or the frontend's ruff/mypy gate. The documents in scope are the root `README.md` and `CLAUDE.md`, `frontend/README.md`, `docs/guides/`, `docs/development/`, `docs/reference/` and `k8s/README.md`.
  - `frontend/README.md` has a "Types (contract)" section with the regeneration workflow from REQ-14:
    - after a backend model change: `uv run python export_openapi.py` in `backend/`, then `npm run gen:api` in `frontend/`, then `npm run typecheck`; fix the drift, and commit the model change, `backend/openapi.json` and `src/api/openapi_gen.ts` together;
    - what `check:api` compares and its exit codes;
    - that the generated file is never hand-edited and is excluded from Biome;
    - why TypeScript is pinned to 6.0.3 and why the `overrides` entry exists.
  - `docs/development/contributing.md` states the same workflow in one paragraph.
- **REQ-14 (API types)**: The frontend's request and response types shall be generated from the backend's OpenAPI schema. They are never hand-written.
  - The backend commits its schema as `backend/openapi.json`. It is produced offline from the FastAPI app (no server, database or LLM) by `backend/export_openapi.py`.
  - A backend unit test fails when `backend/openapi.json` differs from what the app produces.
  - `frontend/src/api/openapi_gen.ts` is generated from `../backend/openapi.json` by `openapi-typescript` and committed. It is never hand-edited, and Biome excludes it.
  - `src/api/types.ts` contains only type aliases over `components['schemas'][…]` from `./openapi_gen`. `Pick`/`Omit` are allowed; restating a field or declaring an `interface` is not.
  - `npm run check:api` exits non-zero when `openapi_gen.ts` is not exactly what `openapi-typescript` produces from the committed snapshot.
  - Renaming or removing a field the UI reads makes `npm run typecheck` fail once the types are regenerated.
  - Generation is never part of `build`, `prebuild`, `postinstall`, `test` or the Dockerfile, because the image's build context is `frontend/` and does not contain `backend/`.

## Contracts

| Contract | Before | After | Breaking? |
|---|---|---|---|
| API models (`backend/app/models/`) | — | None | No |
| OpenAPI snapshot ↔ frontend types (new, REQ-14) | None. The frontend has no types (Python `requests`). | `backend/openapi.json` is the exported schema: `json.dumps(app.openapi(), indent=2, sort_keys=True, ensure_ascii=False)` plus a trailing newline. backend-agent owns it, writes it with `backend/export_openapi.py` and guards it with `backend/tests/unit/openapi_snapshot_test.py`. `frontend/src/api/openapi_gen.ts` is generated from it by `openapi-typescript@7.13.0`. frontend-agent owns it, writes it with `npm run gen:api` and guards it with `npm run check:api`. `src/api/types.ts` aliases `components['schemas'][…]`. | New surface |
| HTTP routes / status codes (backend) | — | None | No |
| Browser-facing routes (new: nginx and the Vite dev proxy) | The browser talks only to Streamlit on `:8502`. The Streamlit pod calls the backend server-side (`utils.py:4-9`). | `GET /` and `/<any non-file path>` serve `index.html`. `/assets/*` serves hashed static files. `/api/v1/*` proxies to `http://${API_HOST}:${API_PORT}` with the URI as sent. `/api/health` proxies to `http://${API_HOST}:${API_PORT}/health`. Any other `/api/*` path returns 404 from nginx and is not proxied. The Vite proxy has the same two API routes and no 404 route (dev only; REQ-9). | New surface |
| `Settings` ↔ backend configmaps | — | None | No |
| Frontend env (`k8s/base/frontend/configmap.yaml`, Vite `API_PROXY_TARGET`) | `API_HOST`, `API_PORT`, read by Python per request from `frontend/frontend.env` (compose `env_file`, from `frontend.env.template`) or the k8s configmap. A bad host fails each request. | Same keys, read by nginx envsubst **at container start**. With a literal hostname, an unresolvable host stops nginx from starting (executed; see *Library behavior*). Source: the k8s configmap (`rag-docs-backend`, `8106`). The frontend has no env file: `frontend/frontend.env.template` is removed (user decision, 2026-10-17), and so is Docker Compose (see the "Docker Compose, `Makefile`, `backend/backend.env.template`" row). The Vite dev proxy reads `API_PROXY_TARGET` from the shell, default `http://localhost:8106` (`frontend/vite.config.ts:5`). | No for keys; yes for behavior on a bad host; the template and the compose source go away |
| Frontend container / Service port | Container 8502, Service 8502, port-forward 8502→8502 | Unchanged: nginx listens on 8502 (`listen 8502;`, `EXPOSE 8502`) instead of the image's default 8080; Service 8502; port-forward 8502→8502 | No |
| Docker Compose, `Makefile`, `backend/backend.env.template` (user decision, 2026-10-17) | `docker-compose.yaml` ran both images with host networking (`--profile backend` or `full`); the backend loaded `env_file: backend/backend.env` (copied from `backend/backend.env.template`) plus `image.env`. The `Makefile` only wrapped `docker compose` (`up`, `build`, `logs`, `down`, …). (`dev` @ `1fbb820`.) | Removed. Kubernetes via Skaffold + minikube is the only way to run the stack. The backend reads process environment variables and the defaults in `backend/app/core/config.py`; `Settings.model_config` sets no `env_file` (`config.py:92-96`), and pydantic-settings 2.6.0 defaults it to `None` (installed `pydantic_settings/main.py:405`). In Kubernetes the variables come from the `backend-config` configmap and the `api-keys` secret through `envFrom` (`k8s/base/backend/deployment.yaml:27-31`). | Yes (run path removed) |
| Frontend image | `python:3.10-slim`, root, Streamlit, `enableCORS`/`enableXsrfProtection` off | Build stage `node:24-alpine` (`npm ci`, `npm run build`). Runtime is `nginxinc/nginx-unprivileged:1.29-alpine`, UID 101, listening on 8502, with `NGINX_ENVSUBST_FILTER=^API_`, the template at `/etc/nginx/templates/default.conf.template` and the shared header include at `/etc/nginx/security-headers.conf`. | Yes (image contents) |
| Frontend probes | None | Readiness and liveness `httpGet` on `/` (port `http`, 8502) with explicit timeouts | No |
| DB schema / Alembic migration | — | None | No |
| Vector DB metadata / collection / table | — | None | No |
| Prompts (`backend/app/prompts/`) | — | None | No |
| CI jobs / gates (`.github/workflows/submission-check.yml`) | `check-format-frontend`: uv plus `ruff format --check`, keyed on `frontend/uv.lock`. The `detect-changes` `frontend` filter is `frontend/**` only (`submission-check.yml:38-39`). | Frontend job `frontend-checks` (replaces `check-format-frontend`): `actions/setup-node` (Node 24, npm cache on `frontend/package-lock.json`), then `npm ci`, `npm run check:api`, `npm run lint` (Biome, `--error-on-warnings`), `npm run typecheck`, `npm test` and `npm run build`. No Python or uv. The `detect-changes` `frontend` filter adds `backend/openapi.json`, so a backend-only PR that changes the schema runs the frontend gate. The workflow `paths:` triggers are unchanged (`backend/**` and `frontend/**` already covered). `backend-unit-tests` is unchanged and runs the new snapshot test through `pytest tests/unit/`. `integration-test.yml` is unchanged but now builds the new image through `skaffold run -p ci,chroma` (`integration-test.yml:120`). The workflow gains a `concurrency` group (`${{ github.workflow }}-${{ github.event.pull_request.number }}`, `cancel-in-progress: true`), per T-4. | Yes (gate commands) |
| Frontend code style (`frontend/biome.jsonc`) | Python: ruff (`frontend/pyproject.toml`) | Biome 2.5.15, pinned exactly, configured per *Design* § Code style (REQ-12). `src/api/openapi_gen.ts` is excluded. | Yes (new gate rules) |
| Frontend toolchain pins (`frontend/package.json`) | — | `typescript` `6.0.3`, `openapi-typescript` `7.13.0` and `@biomejs/biome` `2.5.15`, all exact, plus the `overrides` entry (REQ-1) | New surface |
| Local gate baseline (`.claude/CLAUDE.md`) | Frontend `ruff check .` (I001 baseline) and `mypy .`. Backend `pytest tests/unit`: the note says 130 passed; 154 are collected on `1fbb820` (`pytest tests/unit --collect-only -q`, 2026-10-16). | Frontend: `npm run check:api`, `npm run lint`, `npm run typecheck`, `npm test`, `npm run build`, all clean. Backend: one more unit test (the snapshot test). | Yes (main-session note N-2) |
| `.github/CODEOWNERS` | `/front/` (no such path) | `/frontend/` | No |
| Ownership (`docs/specs/README.md` § Domain agents) | frontend-agent owns `frontend/` except `Dockerfile` | frontend-agent owns `frontend/` except `Dockerfile`, `.dockerignore` and `nginx/`, which belong to k8s-agent. They are deployment config: proxy targets, body limits, headers. | No |

Migration path for the breaking rows: there is no data migration, because the frontend is
stateless. The new image replaces the old one on the next `skaffold run`, on the same port, so
users keep opening `http://localhost:8502`. Developers drop `frontend/.venv` and run `npm ci`.
Anyone who ran the stack with Docker Compose or `make` switches to `skaffold dev` on minikube
(`k8s/README.md`); a local `backend/backend.env` is no longer read by anything.

## Design

### App (`frontend/`, frontend-agent)

The structure follows `.claude/agents/frontend-agent.md`. Every file name is `snake_case` (REQ-12):

```
frontend/
  index.html (lang="es")  package.json  package-lock.json  biome.jsonc  vite.config.ts
  tsconfig.json  tsconfig.app.json  tsconfig.node.json  README.md
  src/main.tsx  src/app.tsx  src/app.module.css  src/app.test.tsx  src/index.css
  src/styles/tokens.css
  src/api/client.ts   createApiClient(fetchImpl, baseUrl = '/api'): health(),
                      ingestDocument(title, contentBase64), ask(documentId, question, strategy)
  src/api/errors.ts   ApiError {kind: 'http' | 'timeout' | 'network', status?, detail?} → copy key
  src/api/openapi_gen.ts  generated by `npm run gen:api`, committed, never hand-edited (REQ-14)
  src/api/types.ts    type aliases over openapi_gen's components['schemas'] (see § API types)
  src/api/index.ts    default client over globalThis.fetch
  src/components/     button, field, card, dropzone, message, sources, status_dot, alert,
                      spinner, empty_state, upload_view, ask_view
                      (each <name>.tsx + <name>.module.css + <name>.test.tsx; exports
                      Button, Field, …, StatusDot, EmptyState, UploadView, AskView)
  src/validation.ts   validateTitle, validatePdf, fileToBase64, formatBytes; shared by both views
                      (+ validation.test.ts)
  src/test/setup.ts  src/test/helpers.ts
```

- **Views.** The app shell has a sticky header (name, nav "Subir PDF · Preguntar", `StatusDot`) and one content column. The active view is kept in the URL hash (`#upload`, `#ask`, default `#upload`), so reload and links keep it. After a successful upload, "Hacer una pregunta →" opens the Ask view with that title filled in. `app.tsx` owns the session state that crosses views: the uploaded-title suggestions (REQ-3) and the per-title threads (REQ-4).
- **Base64.** The base64 is built from the file's `ArrayBuffer` in the browser. The body is about 4/3 of the file size.
- **Limits.** `MAX_PDF_BYTES = 20 * 1024 * 1024` and the client timeouts (`health` 5 s, `ingestDocument` 300 s, `ask` 180 s) are named `CONSTANT_CASE` constants in `src/api/client.ts`.
- **Client signatures.** The client methods take plain arguments and build the snake_case wire bodies (`DocumentIngestRequest`, `AskRequest`) themselves, so snake_case names stay inside `src/api/**` (REQ-12). `k_results` is the client constant `K_RESULTS = 4`, so the exact bodies of AC-3(b) are verified at the client.
- **Validation timing.** A file is validated as soon as it is picked or dropped (its error shows at once) and again at submit. The title and question are validated at submit. Both views use `src/validation.ts`.
- **Field-level errors.** A 404 from `/ask` shows its copy on the "Documento" field and a 413 on the file field. Other failures show an alert, with "Reintentar" only for 5xx, timeout and network errors.
- **Backend status.** `StatusDot` checks `/api/health` on mount and again every 30 s (`RECHECK_MS`). A re-check keeps the current label until it resolves, so "Comprobando…" shows only on first load.
- **Copy.** All strings below are the UI copy (Spanish, REQ-7). *Título* stands for the document title.

| Where | Copy |
|---|---|
| App name | "RAG Docs" (header and `<title>`) |
| Nav / primary buttons | "Subir PDF" (Upload view), "Preguntar" (Ask view); the nav's accessible name is "Principal" |
| Upload fields | "Título"; dropzone "Arrastra un PDF aquí o selecciona un archivo"; the file input's accessible name is "Archivo PDF"; a chosen file shows its name, its size (e.g. "1.4 MB", with a decimal point) and "Quitar" |
| Ask fields | "Documento", "Pregunta", strategy group "Estrategia" with "Estándar" / "Rerank"; hint when Rerank is on: "Rerank no devuelve fuentes." |
| Validation (Upload and Ask): empty or whitespace title | "Escribe un título." |
| Validation (Upload and Ask): `/`, `.` or `..` | "El título no puede contener «/» ni ser «.» o «..»." |
| Validation (Upload and Ask): over 1000 characters | "El título admite como máximo 1000 caracteres." |
| Validation: no file chosen | "Selecciona un archivo PDF." |
| Validation: no `%PDF-` magic | "El archivo no es un PDF." |
| Validation: over `MAX_PDF_BYTES` | "El PDF supera el límite de 20 MB." |
| Validation: empty question | "Escribe una pregunta." |
| Upload loading | "Indexando… los PDF grandes pueden tardar un minuto." |
| Ask loading | hint under the question: "Esto puede tardar unos segundos."; screen-reader text in the answer region: "Buscando respuesta…" |
| Upload 201 | "*Título* indexado. Hacer una pregunta →" |
| Upload 200 `updated` | "*Título* ya estaba indexado. Hacer una pregunta →" |
| Ask empty state | "Haz una pregunta sobre un documento subido." |
| `null` answer | "No se obtuvo respuesta." |
| Empty `source_documents` | "No se devolvieron fuentes." |
| Sources | "Fuentes (n)", "Página N", "Mostrar más" / "Mostrar menos" (long excerpts) |
| Status | "Comprobando…", "Servidor en línea", "Servidor sin conexión" |

- **Error copy** (extends the design skill's mapping). The backend's messages are English and may leak internals, so none is shown:

| Failure | Copy | Shows backend `detail`? |
|---|---|---|
| 400, 422 | "Revisa los datos e inténtalo de nuevo." Highlight the field when known. | No |
| 404 (ask) | "Documento no encontrado. Revisa el título o súbelo primero." | No |
| 413 | "El archivo es demasiado grande para subirlo." | No |
| 504, client timeout | "El servidor tardó demasiado en responder. Inténtalo de nuevo." plus "Reintentar" | No |
| other 5xx, network error | "El servidor no pudo responder. Inténtalo de nuevo." plus "Reintentar" | No (`console.error` only) |

- **Design-skill overrides (the spec wins, per the skill's own rule).** The skill assumes API fields that do not exist:
  - `Sources`: `/ask` sources have no score. Do not render a score or a "similarity" label. Page is "Página `pagina + 1`", omitted when `pagina` is absent. An empty list shows the no-sources note instead of the `<details>` block.
  - Upload success: the API returns no chunk count, so the copy is the 201 row above. A 200 `updated` response gets the 200 row.
  - 409 "Already uploaded" never occurs. A duplicate title is a 200, as above.
  - `EmptyState` example "No documents yet": there is no document list (F-033). The Ask view's empty state is the row above.
  - App shell: the top bar has `min-height: var(--header-h)` instead of a fixed height, and it wraps. At 360 px the status label moves to a second line instead of being clipped. `.main` still subtracts the fixed `--header-h` from `100dvh` (`src/app.module.css:60`), so a wrapped header adds a few pixels of vertical overflow. AC-10 checks horizontal overflow only.
  - Main-session note N-3 amends `SKILL.md` to match once this spec is approved.

### Code style (`frontend/biome.jsonc`, frontend-agent)

`package.json` pins `"@biomejs/biome": "2.5.15"` exactly (`npm i -D -E`): `useConsistentTypeDefinitions`
exists only since 2.1.4, 2.5 deprecates `recommended` in favour of `preset`, and the config below
was verified only against 2.5.15.
Scripts: `"lint": "biome check --error-on-warnings ."` and, for developers,
`"format": "biome check --write ."`. The config below was run against the fixture tree described
in *Library behavior*; frontend-agent may add rules but not weaken these:

```jsonc
{
  "$schema": "./node_modules/@biomejs/biome/configuration_schema.json",
  "files": {
    // src/api/openapi_gen.ts is generated by `npm run gen:api`: never linted or formatted.
    "includes": ["**", "!dist", "!node_modules", "!package-lock.json", "!src/api/openapi_gen.ts"]
  },
  "formatter": { "enabled": true, "indentStyle": "space", "indentWidth": 2, "lineWidth": 100 },
  "javascript": {
    "formatter": { "quoteStyle": "single", "jsxQuoteStyle": "double", "semicolons": "always" }
  },
  "css": { "parser": { "cssModules": true } },
  "assist": { "actions": { "source": { "organizeImports": "on" } } },
  "linter": {
    "enabled": true,
    "rules": {
      "preset": "recommended",
      "suspicious": {
        "noExplicitAny": "error",
        "noDoubleEquals": { "level": "error", "options": { "ignoreNull": true } },
        "noVar": "error",
        "noTsIgnore": "error",
        "noConstEnum": "error"
      },
      "style": {
        "noNonNullAssertion": "error",
        "useImportType": "error",
        "useExportType": "error",
        "useConst": "error",
        "noDefaultExport": "error",
        "useDefaultSwitchClause": "error",
        "useThrowOnlyError": "error",
        "useThrowNewError": "error",
        "useConsistentTypeDefinitions": { "level": "error", "options": { "style": "interface" } },
        "useConsistentArrayType": { "level": "error", "options": { "syntax": "shorthand" } },
        "noNamespace": "error",
        "useFilenamingConvention": {
          "level": "error",
          "options": { "strictCase": true, "requireAscii": true, "filenameCases": ["snake_case"] }
        },
        "useNamingConvention": {
          "level": "error",
          "options": { "strictCase": true, "requireAscii": true }
        }
      }
    }
  },
  "overrides": [
    {
      // Tests may assert non-null.
      "includes": ["**/*.test.ts", "**/*.test.tsx", "src/test/**"],
      "linter": { "rules": { "style": { "noNonNullAssertion": "off" } } }
    },
    {
      // Wire types and fixtures mirror the backend's snake_case JSON.
      "includes": ["src/api/**", "**/*.test.ts", "**/*.test.tsx", "src/test/**"],
      "linter": {
        "rules": {
          "style": {
            "useNamingConvention": {
              "level": "error",
              "options": {
                "strictCase": true,
                "requireAscii": true,
                "conventions": [
                  {
                    "selector": { "kind": "typeProperty" },
                    "formats": ["camelCase", "snake_case"]
                  },
                  {
                    "selector": { "kind": "objectLiteralProperty" },
                    "formats": ["camelCase", "snake_case"]
                  }
                ]
              }
            }
          }
        }
      }
    },
    {
      // Vite requires a default export.
      "includes": ["vite.config.ts"],
      "linter": { "rules": { "style": { "noDefaultExport": "off" } } }
    }
  ]
}
```

Choices where the guide is silent or conflicts with a tool (frontend-agent records them in
`frontend/README.md`, as its agent file requires):

- **Line width 100.** The guide sets no column limit ("code is autoformatted"). 100 matches the backend's ruff (`backend/pyproject.toml:76`).
- **JSX attributes use double quotes** (`jsxQuoteStyle: "double"`, Biome's default and the HTML/React convention). The guide's single-quote rule covers string literals and says nothing about JSX attributes.
- **snake_case wire fields** are allowed only in `src/api/**` and tests (REQ-12), against the guide's `lowerCamelCase` for properties. A camelCase mapping layer would double the type surface for three endpoints.
- **`vite.config.ts` default-exports**, against "Do not use default exports", because Vite requires it.
- **`import styles from './x.module.css'`** is a default *import*, which the guide does not forbid; Vite's CSS modules expose a default export.
- **`src/api/openapi_gen.ts` is excluded from Biome.** It is tool output with double quotes, 4-space indent and lowercase exported interfaces. With the exclusion, the config above was re-run against the generated file plus an alias module, with no errors (*Library behavior*).

### API types (backend-agent, frontend-agent, ci-agent)

The pattern is customs-agent/web's "Types (contract)": a generated file that is committed and
never hand-edited, with `types.ts` aliasing it. One thing differs. customs-agent fetches
`/openapi.json` from a running backend. Here the schema comes from a **snapshot committed by the
backend**, so neither regeneration nor CI needs a running server, Postgres or an LLM, and the
frontend CI job stays Node-only.

**Backend side (backend-agent owns `backend/`).**

- `backend/export_openapi.py` sits beside `main.py`. `backend/admin_chroma.py` is the precedent for a script at the backend root. It is run from `backend/` as `uv run python export_openapi.py`, so `from main import app` resolves without path changes. It exposes:
  - `SNAPSHOT = Path(__file__).with_name("openapi.json")`;
  - `render() -> str`, which returns `json.dumps(app.openapi(), indent=2, sort_keys=True, ensure_ascii=False) + "\n"`;
  - a `__main__` block that writes `render()` to `SNAPSHOT` (UTF-8).

  Exit 0 on success. The script exits non-zero (a Python traceback, exit 1) if the app cannot be imported. `sort_keys` sorts object keys only. The `required` arrays keep declaration order (for example, `SourceDocument.required` is `["page_content", "metadata"]` in the dump), so reordering the required fields of a model changes the snapshot and fails the test until it is re-exported.
- `backend/openapi.json` is the committed output.
- `backend/tests/unit/openapi_snapshot_test.py` asserts `SNAPSHOT.read_text(encoding="utf-8") == render()`. Its failure message names both regeneration commands. It runs in every `pytest tests/unit` (the backend-agent gate and the `backend-unit-tests` CI job), so a model change without a regenerated snapshot fails there.
  - That `from export_openapi import …` resolves under pytest is **inferred** from existing tests that `from main import app` (for example `backend/tests/unit/api/health_router_test.py`). It was run only from the scratchpad with `PYTHONPATH=.`.
- Prototyped in the scratchpad against the backend venv on 2026-10-16:
  - the script's output is byte-identical to the dumps in *Context*;
  - the test passed, then failed once the snapshot was edited;
  - `ruff check`, `ruff format --check` (with `backend/pyproject.toml`) and `mypy` on the script were clean.

**Frontend side (frontend-agent owns `frontend/`).**

The `package.json` scripts call the CLI directly, so there are no `.mjs` helper scripts:

```json
"gen:api": "openapi-typescript ../backend/openapi.json -o src/api/openapi_gen.ts",
"check:api": "openapi-typescript ../backend/openapi.json -o src/api/openapi_gen.ts --check"
```

- `gen:api` writes the file and exits 0. It exits 1 if the snapshot is missing or invalid.
- `check:api` writes nothing. It exits 0 when the file is current, and 1 when it is stale, missing, or the snapshot is unreadable (*Library behavior*). Both run from `frontend/`, the directory npm runs scripts in.
- `src/api/types.ts` contains only aliases:

```ts
import type { components } from './openapi_gen';

type Schemas = components['schemas'];

export type DocumentIngestRequest = Schemas['DocumentIngestRequest'];
export type DocumentIngestResponse = Schemas['DocumentIngestResponse'];
/** The ask body the UI sends (AC-3b): the schema marks every defaulted field as required. */
export type AskRequest = Pick<Schemas['QuestionRequest'], 'question' | 'strategy' | 'k_results'>;
export type Strategy = Schemas['QuestionRequest']['strategy'];
export type QuestionAnswerResponse = Schemas['QuestionAnswerResponse'];
export type SourceDocument = Schemas['SourceDocument'];
```

What the generated types say, which the client and components must handle. Generation was executed from the snapshot, and the models were read in `backend/app/models/`:

- `QuestionRequest` has `strategy`, `k_results` and `metadata_filter` **required**, because they have defaults (`search_request.py:16-22`). Use `AskRequest`, so the body stays exactly `{question, strategy, k_results}` (AC-3b).
- `QuestionAnswerResponse.source_documents` is **optional**, because it is a `default_factory` (`qa_response.py:19-21`). Treat a missing value as `[]`.
- `answer` is `string | null` (`qa_response.py:14-16`).
- `SourceDocument.metadata` is `{ [key: string]: unknown }` (`qa_response.py:8`). Narrow `pagina` with `typeof … === 'number'` before showing "Página N". `score` is `number | null` and optional.
- `DocumentIngestRequest.document_type` is `string | null`. `DocumentIngestResponse.status` is `'created' | 'updated'`.
- `/health` has no response schema. The client types only the HTTP status (REQ-6).

**Drift matrix.**

| Change | Fails | Where |
|---|---|---|
| Backend model changed, `backend/openapi.json` not regenerated | `openapi_snapshot_test.py` | `pytest tests/unit` locally; `backend-unit-tests` in CI |
| Snapshot regenerated, `openapi_gen.ts` not | `npm run check:api` (exit 1) | frontend gate locally; the frontend CI job, triggered by `backend/openapi.json` (REQ-11) |
| `openapi_gen.ts` hand-edited | `npm run check:api` (exit 1) | same |
| Types regenerated, UI still reads a renamed or removed field | `npm run typecheck` (`tsc -b`) | frontend gate; the frontend CI job |
| `openapi-typescript` version bumped, output changes | `npm run check:api` until `gen:api` is re-run | same |

**Not wired into the build.** `npm run build` (`tsc -b && vite build`) and the Docker build read
the committed `openapi_gen.ts`. They never run `gen:api` (REQ-14), because the image's build
context is `frontend/` and has no `../backend/openapi.json`.

### Serving (`frontend/Dockerfile`, `frontend/.dockerignore`, `frontend/nginx/default.conf.template`, `frontend/nginx/security-headers.conf`, k8s-agent)

The config is modelled on `customs-agent/web/nginx.conf`, with these differences:

- **Port.** `listen 8502;` (and `EXPOSE 8502`), replacing the image's default 8080, so the container, Service and port-forward keep today's port. 8502 is above 1024, so UID 101 can bind it.
- **Upstream from env.** The template uses `${API_HOST}` and `${API_PORT}`, and the image's envsubst step renders it at start. Setting `NGINX_ENVSUBST_FILTER` to `^API_` is recommended, so no other variable is ever substituted.
- **Routes:**
  - `location /api/v1/ { proxy_pass http://${API_HOST}:${API_PORT}; }` has no URI, so encoded titles reach uvicorn as sent.
  - `location = /api/health { proxy_pass http://${API_HOST}:${API_PORT}/health; }`
  - `location /api/ { return 404; }`, so an unknown `/api/*` path is not served `index.html`.
  - `location /assets/` uses an immutable cache.
  - `location / { try_files $uri /index.html; }`, with `Cache-Control: no-cache`.
- **No SSE settings** (`proxy_buffering off`, as in the reference). They are not needed.
- **Limits:**
  - `client_max_body_size 30m`. The largest body is ⌈`MAX_PDF_BYTES` × 4/3⌉ = 27,962,027 bytes plus about 1 KB of JSON, below `30m` whether nginx counts `m` as 10⁶ or 2²⁰ bytes.
  - `proxy_read_timeout` and `proxy_send_timeout` `300s`, at least the longest client timeout.
  - `client_body_timeout` is `120s`.
- **Headers** (`always`), in `frontend/nginx/security-headers.conf`, which every location includes. nginx does not inherit `add_header` into a location that sets its own (`/assets/` and `/` set `Cache-Control`), so the template has no server-level `add_header`:
  - `X-Content-Type-Options nosniff`
  - `Referrer-Policy no-referrer`
  - `X-Frame-Options DENY`
  - `Content-Security-Policy "default-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"`. `data:` covers small assets that Vite inlines.
  - QA checks the browser console for CSP violations (AC-10).
- **XSRF (F-029).** The new app uses no cookies or credentials, and the backend has no CORS middleware (`backend/main.py`). A cross-origin page therefore cannot read API responses. XSRF tokens are not applicable, and the Streamlit flags disappear with Streamlit.
- **Image.** The build stage is `node:24-alpine` (`npm ci`, `npm run build`). The runtime is `nginxinc/nginx-unprivileged:1.29-alpine`. `.dockerignore` excludes `node_modules`, `dist` and `*.env`.
- **Kubernetes:**
  - Container port 8502 (named `http`) and Service port/targetPort 8502, as today. The skaffold port-forward stays 8502→8502.
  - Probes use `httpGet /` on the `http` port. That path is static, so the frontend's readiness does not depend on the backend.
  - Resources are sized for nginx: proposed requests `32Mi`/`10m`, limits `128Mi`/`200m`.
  - The configmap keeps `API_HOST: rag-docs-backend` and `API_PORT: "8106"`. The Service DNS name exists once the Service object is applied, and skaffold applies all manifests before pods start (inferred).
- **Compose.** Removed, together with the `Makefile` and `backend/backend.env.template` (user decision, 2026-10-17). The frontend has no env file or template.

### Alternatives considered

- **Keep Streamlit and fix F-028/F-029 in place.** Rejected because the user asked for a replacement.
- **CORS on the backend, with the browser calling it directly.** Rejected: it needs a backend change, bakes a backend URL into the bundle, and widens the attack surface.
- **A runtime `config.js` holding the backend URL.** Not needed: same-origin removes every client-side setting.
- **Next.js or another SSR framework.** Rejected: there is no server rendering need, it costs a Node runtime image, and the reference uses Vite.
- **nginx on its default 8080 with a remapped Service.** Rejected by the user (open question 3): keeping 8502 end to end leaves every variable and URL unchanged.
- **camelCase domain types mapped from the snake_case wire types.** Rejected as disproportionate (see *Code style*).
- **Hand-written `types.ts` (open question 9, option a).** Rejected by the user in favour of generated types.
- **Generate from a running backend's `/openapi.json`, as customs-agent does.** Rejected: both regeneration and the CI drift check would need the backend plus Postgres running. The schema dumps offline, so a committed snapshot needs neither.
- **The frontend CI job sets up uv and the backend venv to dump the schema live.** Rejected: it couples the frontend job to the Python toolchain. The snapshot test already catches backend-side drift in the backend job.
- **Snapshot under `frontend/`.** Rejected: ownership is exclusive, so every backend model change would need a frontend-agent step just to copy the schema. The producer owns the snapshot.
- **A separate `--check` mode in the export script plus a new CI step.** Rejected in favour of a unit test, which runs in the existing `backend-unit-tests` job and in every backend-agent local gate, with no workflow change on the backend side.
- **Porting customs-agent's `gen-api.mjs`/`check-api.mjs`.** Not needed: the CLI's built-in `--check` does the comparison. Helper scripts would also need snake_case names under REQ-12.
- **TypeScript 7.** Rejected for now: openapi-typescript 7.13.0 crashes on it (*Library behavior*). See open question 10.

## Acceptance criteria

The ACs avoid live LLM calls. AC-9 and AC-10 need a deployed `local,chroma` stack, with Ollama
served on the host as in `k8s/README.md` § "Run ollama on the host" (`configmap-local.yaml:14-16`
sets `LOCAL_LLM=true` and `OLLAMA_BASE_URL=http://host.minikube.internal:11434`). They call the
embeddings model (ingest and search) but never LLM generation. Asking a question in the browser
against the stack is a non-gating QA step (T-6). Commands for each AC are in the fenced blocks
below the table. Run each command separately. UI text asserted below is the Spanish copy from
*Design*.

| ID | Given / When / Then | Verified by |
|---|---|---|
| AC-1 | The Streamlit app is gone: no Python file, `pyproject.toml` or `uv.lock` is tracked under `frontend/`. | Command block AC-1 → no output |
| AC-2 | The frontend gate passes from a clean install. | Command block AC-2: every command exits 0 (`npm run lint` uses `--error-on-warnings`, so exit 0 means no warnings or errors); vitest reports 0 failed; `dist/index.html` exists and declares `lang="es"` |
| AC-3 | The API client (a) builds `/api/v1/documents/a%20b%3F%23c/ask` for title `a b?#c`; (b) sends the ingest body `{title, document_type: 'documento-pdf', document_content}` and the ask body `{question, strategy, k_results: 4}` with exactly those fields; (c) aborts at its timeout and raises `ApiError` with kind `timeout` (fake timers); (d) maps non-2xx to kind `http` with the status; (e) maps a rejected fetch to kind `network`; (f) calls `/api/health` for health. | `frontend/src/api/client.test.ts` |
| AC-4 | Error copy: 400, 404, 413, 422, 500, 504, timeout and network each map to the copy in *Design*. For 500 the rendered text does not contain the response `detail`. | `frontend/src/api/errors.test.ts` and `frontend/src/components/ask_view.test.tsx` |
| AC-5 | Upload validation blocks the request (fetch not called) and shows the *Design* validation copy for each of: empty title, whitespace-only title, a title with `/`, title `.`, title `..`, a title of 1001 characters, a file without `%PDF-` magic bytes, and a file of `MAX_PDF_BYTES + 1` bytes. A title of 1000 characters and a file of exactly `MAX_PDF_BYTES` are accepted (fetch called). The title is sent trimmed. A 201 shows "*title* indexado." and a 200 `updated` shows "*title* ya estaba indexado.", each with the "Hacer una pregunta →" action. | `frontend/src/components/upload_view.test.tsx` |
| AC-6 | The Ask view: Enter submits and Shift+Enter does not. The title is trimmed before the request. The strategy defaults to `standard`; selecting "Rerank" sends `rerank`. `k_results: 4` is added by the client and verified by AC-3(b). An empty title or question blocks the request (`ask` not called) and shows its *Design* validation copy. The Ask view validates the title with the same `validateTitle` as the Upload view, and `validation.test.ts` covers its `/`, `.`, `..` and 1001-character cases. An answer containing `<b>x</b>` renders that literal text with no `<b>` element. Sources show "Página 3" for `pagina: 2` and no score. `source_documents: []` shows "No se devolvieron fuentes.". A `null` answer shows "No se obtuvo respuesta.". A 404 shows "Documento no encontrado". Two consecutive questions both stay visible. The answer region has `aria-live="polite"`. | `frontend/src/components/ask_view.test.tsx`; `frontend/src/validation.test.ts` for the title rules |
| AC-7 | `StatusDot` shows "Comprobando…", then "Servidor en línea" for 200, and "Servidor sin conexión" for 503, timeout and network error. | `frontend/src/components/status_dot.test.tsx` |
| AC-8 | The image builds, runs as UID 101, exposes and listens on 8502 (the base image's inherited `8080/tcp` may also appear in `ExposedPorts`; nothing listens on it), starts with an IP upstream, sends the security headers, falls back to `index.html`, and returns 404 with the security headers for an unknown `/api/*` path. | Command block AC-8 |
| AC-9 | Deployed stack: all deployments stabilize. The frontend readiness probe is on `/`. Through the frontend port-forward on 8502, `/` serves the app, `/api/health` reaches the backend, a 2.5 MB ingest body is accepted (never `413`), and an encoded title with space, `?` and `#` reaches `/search`. | Command block AC-9 |
| AC-10 | Browser check of the design checklist on the deployed stack (AC-9 setup), at 360, 768 and 1280 px, in light and dark (`prefers-color-scheme` emulation): `document.documentElement.scrollWidth <= window.innerWidth` on both views; exactly one primary button per view; all visible copy is Spanish and matches the *Design* copy table (the exceptions are the terms "PDF" and "Rerank", the product name "RAG Docs", and file sizes such as "1.4 MB"); a keyboard-only upload of `backend/tests/behave/data/ros-intro.pdf` succeeds (Tab order, visible focus, Enter submits); no CSP violation in the console; `StatusDot` reads "Servidor en línea". | qa-agent with the Playwright MCP browser (QA tooling, not a project dependency): screenshots per width and theme, plus the console log, recorded in *Verification* |
| AC-11 | The local dev proxy mirrors nginx's health route. | Command block AC-11 |
| AC-12 | The Kubernetes config lints clean and keeps port 8502. | Command block AC-12 |
| AC-13 | The CI workflow defines the npm frontend gate, `check:api` included, and the `detect-changes` `frontend` filter includes `backend/openapi.json`. No Python frontend job remains. | Command block AC-13. The workflow's runtime result is **non-gating**: CI runs only on the PR, which is opened after `Done`. QA records the expected check, `gh run list --branch spec/SPEC-002-web-frontend --workflow submission-check.yml`, and the PR author confirms it. |
| AC-14 | No in-scope doc describes the old frontend, and CODEOWNERS points at `frontend/`. | Command block AC-14 → no output |
| AC-15 | `npm run lint` enforces REQ-12: Biome is pinned at 2.5.15; probe files that break the file-name, default-export, `any`, non-null and formatting rules make lint exit non-zero and name each rule; with the probes removed lint exits 0; no `@ts-ignore`, `@ts-expect-error` or `@ts-nocheck` and no file name with an uppercase letter exists under `src/`. | Command block AC-15 |
| AC-16 | Session state across views: with `#ask` in the URL the Ask view renders. After a mocked 201 upload of "Manual A" and a mocked 200 `updated` upload of "Manual B", the Ask title field's `<datalist>` holds both titles, and "Hacer una pregunta →" opens `#ask` with the title filled in. A question asked on "Manual A", then the title changed to "Manual B" and back, shows "Manual A"'s thread again; switching to `#upload` and back keeps it. Nothing is written to `localStorage` or `sessionStorage`. | `frontend/src/app.test.tsx` |
| AC-17 | API types are generated and wired per REQ-14 and REQ-1:<br>• `typescript` is `6.0.3`, `openapi-typescript` is `7.13.0`, and the `overrides` entry is present;<br>• `gen:api` and `check:api` are the exact strings in *Design* § API types;<br>• no `build`, `prebuild`, `postinstall` or `test` script and no Dockerfile line runs `openapi-typescript`;<br>• `openapi_gen.ts` carries the openapi-typescript header, is excluded in `biome.jsonc`, and is the only module `types.ts` imports;<br>• `types.ts` declares no `interface`;<br>• the backend snapshot test passes;<br>• `check:api` exits 0. | Command block AC-17 |
| AC-18 | Drift fails in both directions and clears after regenerating:<br>• a deliberate rename of `SourceDocument.page_content` makes the backend snapshot test fail;<br>• after `export_openapi.py` the test passes, and `check:api` exits 1;<br>• after `gen:api`, `check:api` exits 0 and `typecheck` fails, naming `page_content`;<br>• after the rename is reverted and both files are regenerated, both files match their originals byte for byte, and `check:api` and `typecheck` exit 0. | Command block AC-18 |

`<scratch>` below is any writable directory outside the repo (QA's scratchpad).

```bash
# AC-1 (repo root) -> no output
git ls-files frontend | grep -E '\.py$|pyproject\.toml$|uv\.lock$'

# AC-2 (in frontend/), each separately
npm ci
npm run check:api
npm run lint
npm run typecheck
npm test
npm run build
test -f dist/index.html && echo ok          # -> ok
grep -c '<html lang="es"' dist/index.html   # -> 1

# AC-8 (repo root; Docker running)
docker build -t rag-docs-frontend:spec002 frontend                     # -> exit 0
docker run --rm --entrypoint id rag-docs-frontend:spec002 -u            # -> 101
docker inspect -f '{{json .Config.ExposedPorts}}' rag-docs-frontend:spec002 | grep -c '"8502/tcp"'   # -> 1 (8080/tcp is inherited from the base image)
docker run -d --name fe002 -e API_HOST=127.0.0.1 -e API_PORT=8106 -p 18080:8502 rag-docs-frontend:spec002
docker exec fe002 netstat -ltn                                          # -> exactly one LISTEN line, 0.0.0.0:8502
curl -sI http://localhost:18080/
#   -> HTTP 200, with x-content-type-options: nosniff, referrer-policy: no-referrer, content-security-policy: ...
curl -s http://localhost:18080/some/route | grep -c 'id="root"'         # -> 1
curl -sI http://localhost:18080/api/unknown
#   -> HTTP 404, with x-content-type-options: nosniff, referrer-policy: no-referrer, content-security-policy: ...
docker rm -f fe002

# AC-9 (repo root; minikube running, Ollama served on the host)
skaffold run -p local,chroma -f skaffold.yaml                           # -> exit 0, deployments stabilized
kubectl get deploy rag-docs-frontend -o jsonpath='{.spec.template.spec.containers[0].readinessProbe.httpGet.path}'   # -> /
(cd backend && uv run --offline python -c "import os,sys,fitz; d=fitz.open(); d.new_page().insert_text((72,72),'SPEC-002 large upload probe'); pix=fitz.Pixmap(fitz.csRGB,800,800,os.urandom(800*800*3),False); d.new_page().insert_image(fitz.Rect(0,0,595,842),pixmap=pix); d.save(sys.argv[1])" <scratch>/large.pdf)
python3 -c "import base64,json,sys; b=open(sys.argv[1],'rb').read(); json.dump({'title':'spec002 large ?#','document_type':'documento-pdf','document_content':base64.b64encode(b).decode()}, open(sys.argv[2],'w'))" <scratch>/large.pdf <scratch>/body.json
ls -l <scratch>/body.json                                               # -> about 2.5 MB (> 1 MB nginx default)
kubectl port-forward svc/rag-docs-frontend 8502:8502 &
curl -s localhost:8502/ | grep -c 'id="root"'                           # -> 1
curl -s localhost:8502/api/health                                       # -> {"status":"healthy",...}
curl -s -o /dev/null -w '%{http_code}\n' -X POST localhost:8502/api/v1/documents \
  -H 'content-type: application/json' --data @<scratch>/body.json       # -> 201 (200 on re-run), never 413
curl -s -X POST 'localhost:8502/api/v1/documents/spec002%20large%20%3F%23/search' \
  -H 'content-type: application/json' -d '{"query":"upload probe","k_results":1}'   # -> 200, "total_results":1

# AC-11 (backend reachable on localhost:8106, e.g. kubectl port-forward svc/rag-docs-backend 8106:8106)
cd frontend && npm run dev -- --port 5173 --strictPort &
curl -s localhost:5173/api/health                                       # -> {"status":"healthy",...}

# AC-12 (repo root)
uvx yamllint -d relaxed k8s skaffold.yaml                               # -> exit 0
skaffold render -p local,chroma --digest-source=none -f skaffold.yaml | grep -A12 'name: rag-docs-frontend'
#   -> containerPort: 8502, Service port: 8502 and targetPort 8502 (or the port name `http`)
grep -nE 'localPort|port:' k8s/base/frontend/skaffold.yaml              # -> port-forward 8502 -> 8502

# AC-13 (repo root)
uvx --from actionlint-py actionlint                                     # -> exit 0
uvx yamllint -d relaxed .github                                         # -> exit 0
grep -cE 'npm (ci|run check:api|run lint|run typecheck|test|run build)' .github/workflows/submission-check.yml   # -> 6 or more
grep -c 'npm run check:api' .github/workflows/submission-check.yml      # -> 1 or more
grep -nE 'backend/openapi\.json' .github/workflows/submission-check.yml # -> a line under the detect-changes `frontend:` filter (confirm by eye)
grep -n 'frontend/uv.lock' .github/workflows/submission-check.yml       # -> no output

# AC-14 (repo root) -> no output from either
grep -rnEi 'streamlit|8501|front\.py|ruff check \.' README.md CLAUDE.md frontend/README.md docs/guides docs/development docs/reference k8s/README.md
grep -n '/front/' .github/CODEOWNERS

# AC-15 (in frontend/, after npm ci), each separately
node -p "require('./package.json').devDependencies['@biomejs/biome']"   # -> 2.5.15
node -p "require('./package.json').scripts.lint"                        # -> biome check --error-on-warnings .
printf 'export const probeValue = 1;\n' > src/BadName.ts
printf 'const probeValue = 1;\nexport default probeValue;\n' > src/default_probe.ts
printf 'export function anyProbe(x: any): string {\n  return x;\n}\n' > src/any_probe.ts
printf 'export function nonNullProbe(x?: string): number {\n  return x!.length;\n}\n' > src/non_null_probe.ts
printf 'export const formatProbe = "a"\n' > src/format_probe.ts
npm run lint > <scratch>/lint.txt 2>&1; echo $?                         # -> non-zero
grep -oE 'lint/(style|suspicious)/(useFilenamingConvention|noDefaultExport|noExplicitAny|noNonNullAssertion)' <scratch>/lint.txt | sort -u   # -> 4 lines
grep -cE 'src/format_probe\.ts format' <scratch>/lint.txt               # -> 1
rm src/BadName.ts src/default_probe.ts src/any_probe.ts src/non_null_probe.ts src/format_probe.ts
npm run lint                                                            # -> exit 0
grep -rnE '@ts-(ignore|expect-error|nocheck)' src                       # -> no output
find src -name '*[A-Z]*'                                                # -> no output

# AC-17 (in frontend/, after npm ci), each separately
node -p "require('./package.json').devDependencies.typescript"          # -> 6.0.3
node -p "require('./package.json').devDependencies['openapi-typescript']"   # -> 7.13.0
node -p "JSON.stringify(require('./package.json').overrides)"           # -> {"openapi-typescript":{"typescript":"$typescript"}}
node -p "require('./package.json').scripts['gen:api']"                  # -> openapi-typescript ../backend/openapi.json -o src/api/openapi_gen.ts
node -p "require('./package.json').scripts['check:api']"                # -> openapi-typescript ../backend/openapi.json -o src/api/openapi_gen.ts --check
node -p "const s=require('./package.json').scripts; ['build','prebuild','postinstall','test'].filter(k=>/openapi-typescript|gen:api/.test(s[k]??'')).length"   # -> 0
grep -c 'openapi-typescript\|gen:api' Dockerfile                        # -> 0
grep -c 'auto-generated by openapi-typescript' src/api/openapi_gen.ts   # -> 1
grep -c '!src/api/openapi_gen.ts' biome.jsonc                           # -> 1
grep -nE "^import " src/api/types.ts                                    # -> one line: import type { components } from './openapi_gen';
grep -nE '\binterface\b' src/api/types.ts                               # -> no output
npm run check:api; echo $?                                              # -> 0
(cd ../backend && uv run pytest tests/unit/openapi_snapshot_test.py -q) # -> 1 passed

# AC-18 (repo root). The files are uncommitted while QA runs, so restore from backups, never git.
git diff --quiet -- backend/app/models/responses/qa_response.py; echo $?   # -> 0 (unchanged, safe to revert with git)
cp backend/openapi.json frontend/src/api/openapi_gen.ts <scratch>/
perl -pi -e 's/^    page_content: str/    content_text: str/' backend/app/models/responses/qa_response.py
(cd backend && uv run pytest tests/unit/openapi_snapshot_test.py -q)   # -> 1 failed; message names export_openapi.py
(cd backend && uv run python export_openapi.py)                         # -> exit 0
(cd backend && uv run pytest tests/unit/openapi_snapshot_test.py -q)   # -> 1 passed
(cd frontend && npm run check:api); echo $?                              # -> 1, "Generated types are not up-to-date!"
(cd frontend && npm run gen:api && npm run check:api); echo $?           # -> 0
(cd frontend && npm run typecheck); echo $?                              # -> non-zero; an error naming 'page_content'
git checkout -- backend/app/models/responses/qa_response.py
(cd backend && uv run python export_openapi.py) && (cd frontend && npm run gen:api)
cmp backend/openapi.json <scratch>/openapi.json && cmp frontend/src/api/openapi_gen.ts <scratch>/openapi_gen.ts && echo restored   # -> restored
(cd frontend && npm run check:api && npm run typecheck); echo $?         # -> 0
```

## Tasks

The API itself is unchanged, but its schema becomes a contract (REQ-14), so it lands first: T-7
commits the backend's OpenAPI snapshot. The app (T-1) generates its types from that snapshot, and
its Vite proxy pins the route contract. Deployment and CI then consume both. T-7 keeps a new ID so
the existing task references stay stable. It is listed first because it runs first.

| ID | Task | Agent | Depends on | Files | Status |
|---|---|---|---|---|---|
| T-7 | Add the OpenAPI snapshot per REQ-14 and *Design* § API types: `export_openapi.py` (`SNAPSHOT`, `render()`, `__main__`), the generated `openapi.json`, and `tests/unit/openapi_snapshot_test.py` with a failure message that names `uv run python export_openapi.py` (in `backend/`) and `npm run gen:api` (in `frontend/`). Add one line to `backend/README.md` on regenerating after a model change. No change under `backend/app/`. Gate: `uv run ruff check export_openapi.py tests/unit/openapi_snapshot_test.py`, `uv run ruff format --check .`, `uv run mypy export_openapi.py`, and `uv run pytest tests/unit` with the snapshot test passing. Also run the snapshot test after a temporary edit to `openapi.json` to confirm it fails, then restore. | backend-agent | — | `backend/export_openapi.py`, `backend/openapi.json`, `backend/tests/unit/openapi_snapshot_test.py`, `backend/README.md` | Done |
| T-0 | At approval, before any implementation: move `frontend/.dockerignore` and `frontend/nginx/` to k8s-agent in the ownership table (pairs with main-session note N-4). | architect | — | `docs/specs/README.md` | Done |
| T-1 | Build the web app per REQ-1–REQ-7, REQ-9, REQ-12 and REQ-14, and *Design* § App, § Code style and § API types, with all copy in Spanish. Pin `typescript`, `openapi-typescript` and Biome exactly, and add the `overrides` entry. Add the `gen:api`/`check:api` scripts, generate `src/api/openapi_gen.ts` from T-7's snapshot, and write `src/api/types.ts` as aliases only. Write the tests named in AC-3–AC-7 and AC-16. Run the AC-15 probe and the frontend half of AC-18. Delete the Streamlit app. Rewrite `frontend/README.md`: commands, structure, a reason for each dev dependency, the API assumptions above, the style choices listed under *Code style*, and the "Types (contract)" section from REQ-13. Run the design checklist at 360/768/1280 against `npm run dev` with a port-forwarded backend. | frontend-agent | T-0, T-7, N-1, N-4 | `frontend/{package.json,package-lock.json,biome.jsonc,vite.config.ts,tsconfig*.json,index.html,README.md}`, `frontend/src/**`, `frontend/public/**`; delete `frontend/{front.py,components/,utils/,pages/,src/__init__.py,data/,pyproject.toml,uv.lock}` | Done |
| T-2 | Serve and deploy per REQ-8 and REQ-10 and *Design* § Serving: Dockerfile (`EXPOSE 8502`; it builds from the committed `src/api/openapi_gen.ts` and never runs `gen:api`, per REQ-14), `.dockerignore`, nginx template (`listen 8502`), frontend manifests (container and Service stay on 8502, port named `http`; port-forward stays 8502→8502), probes and resources, configmap comment. The frontend has no env file, and Docker Compose is removed (both 2026-10-17). Gate: yamllint, `skaffold render`, `docker build`, and AC-8. | k8s-agent | T-0, N-4, T-1 | `frontend/Dockerfile`, `frontend/.dockerignore`, `frontend/nginx/default.conf.template`, `frontend/nginx/security-headers.conf`, `k8s/base/frontend/{deployment,service,configmap,skaffold}.yaml`; delete `frontend/frontend.env.template`, `docker-compose.yaml` and `backend/backend.env.template` (2026-10-17) | Done |
| T-3 | Update the setup guide and the k8s README: prerequisites (Node 24 and npm for frontend dev), the frontend env section (nginx upstream, start-time resolution), local dev (`npm ci && npm run dev`, proxy target override) and the frontend URL (`http://localhost:8502`, unchanged). | k8s-agent | T-2 | `docs/guides/setup.md`, `k8s/README.md` | Done |
| T-4 | Replace the frontend Python CI job with the Node gate (REQ-11, AC-13), with `npm run check:api` after `npm ci`. Add `backend/openapi.json` to the `detect-changes` `frontend` filter. The frontend job installs no Python or uv. `backend-unit-tests` stays as is: it already runs the snapshot test. Add `concurrency` if absent. Fix CODEOWNERS. Update the dev docs: frontend install; gate commands (`check:api`, Biome lint and format, typecheck, vitest, build); the code-style reference (Google TS Style Guide via `frontend/biome.jsonc`); test layout; and, in `contributing.md`, the API-types regeneration workflow (REQ-13). | ci-agent | T-1, T-7 | `.github/workflows/submission-check.yml`, `.github/CODEOWNERS`, `docs/development/testing.md`, `docs/development/contributing.md` | Done |
| T-5 | Update the project docs: Stack, Frontend and Common Commands in `CLAUDE.md`; feature list, URL and structure in `README.md`; a Frontend section in `architecture.md` covering the same-origin proxy, routes and why titles cannot contain `/` or be `.`/`..`. | architect | T-2 | `README.md`, `CLAUDE.md`, `docs/reference/architecture.md` | Done |
| T-6 | Verify AC-1–AC-18 (AC-13's PR-run check is non-gating). AC-18 edits `qa_response.py` temporarily; restore it and the generated files exactly as its command block says, and record `git status --short` before and after. AC-10 is a real-browser check (Playwright MCP) at 360/768/1280, light and dark. The non-gating step: ask one question about `ros-intro.pdf` in the browser against the stack, record the outcome, and do not let it fail the spec. No new behave scenarios: the API is unchanged. | qa-agent | T-1–T-5, T-7, N-2 | spec *Verification*, finding *Status* | Done |

### Main-session notes (files outside every domain agent's ownership)

- **N-1 (before T-1).** Root `.gitignore` does not ignore `frontend/node_modules` or `frontend/dist`. `git check-ignore -v frontend/node_modules/x frontend/dist/x` prints nothing. Line 39 also ignores any nested `.gitignore` (`git check-ignore -v frontend/.gitignore` → `.gitignore:39`), so the frontend cannot ship its own. Add `node_modules/` and `frontend/dist/` to the root `.gitignore`.
- **N-2 (after T-1, T-4 and T-7).** Update the gate baseline in `.claude/CLAUDE.md`:
  - Replace the frontend line with the npm gate (`npm run check:api`, `npm run lint`, `npm run typecheck`, `npm test`, `npm run build`, expected clean).
  - Refresh the backend `pytest tests/unit` count. The note says 130 passed. 154 are collected on `1fbb820`, and T-7 adds one, so 155 are expected; take the number from T-7's gate run.
  - Add `uv run python export_openapi.py` to the backend workflow for model changes.
- **N-3 (after approval).** Amend `.claude/skills/design/SKILL.md` per *Design* § overrides: no score on `/ask` sources, no chunk count, 200 `updated` instead of 409, the empty-state copy, 413/504 in the error mapping, and Spanish as this app's UI language.
- **N-4 (at approval, before T-1).** Update the ownership lines in `.claude/agents/frontend-agent.md` and `.claude/agents/k8s-agent.md`: `frontend/.dockerignore` and `frontend/nginx/` go to k8s-agent. This is required before T-1 and T-2, so neither agent refuses a path and QA's diff review does not flag one. Remove the frontend-agent "Migration note" once this spec is `Done`.
- **N-5 (2026-10-17, user decision).** Delete the root `Makefile`. It only wrapped `docker compose`, which is removed, and no domain agent owns it.

## Open questions

All questions were decided by the user on 2026-10-16.

- [x] **1. UI language.** *Decided*: Spanish, the current app's language (`front.py:12-13`, `chatbot.py:10-13`, `qa_pdf.py:10-17`). All copy is in *Design*; identifiers, file names and URL hashes stay English (REQ-7).
- [x] **2. Document selection.** *Decided*: free-text title with this session's uploaded titles as `<datalist>` suggestions, no backend change (REQ-3, AC-16). The picker fed by a new `GET /api/v1/documents` is deferred to a later spec and tracked as [F-033](../findings/F-033-no-document-list.md).
- [x] **3. Container/Service port.** *Decided*: keep 8502 everywhere (container, Service, port-forward, compose); nginx listens on 8502 instead of its default 8080. The port contract is now non-breaking.
- [x] **4. Dark mode.** *Decided*: light and dark follow `prefers-color-scheme`, no toggle.
- [x] **5. Test scope.** *Decided*: vitest and Testing Library unit tests only; no Playwright, no mock mode. The real-browser check stays QA's AC-10.
- [x] **6. Upload size limit and timeouts.** *Decided*: `MAX_PDF_BYTES` = 20 MiB; nginx `client_max_body_size 30m`; client timeouts health 5 s, ingest 300 s, ask 180 s; nginx `proxy_read_timeout`/`proxy_send_timeout 300s`. No body limit is configured in the backend (`backend/main.py`, `backend/Dockerfile:28`); uvicorn and Starlette library limits were not verified.
- [x] **7. Strategy and `k` in the UI** (F-028 follow-up "Strategy/k selector"). *Decided*: a secondary "Estándar / Rerank" control defaulting to Estándar, with `k` fixed at 4. F-028's selector item is split: strategy closes with this spec; `k` is out of scope by user decision.
- [x] **8. Chat history.** *Decided*: in memory for the page session, kept per document title, cleared on reload (REQ-4).
- [x] **9. API types.** *Decided*: (b), generated types modelled on customs-agent/web. The toolchain coupling that the earlier recommendation of (a) worried about is avoided: the backend commits an offline schema snapshot, a backend unit test keeps it current, and the frontend job diffs against it with Node only (REQ-14, *Design* § API types). This also needs the exact TypeScript pin `6.0.3` and the `overrides` entry (REQ-1).
- [x] **10. TypeScript 7.** *Decided*: stay on 6.0.3 for this spec; no follow-up until openapi-typescript supports TS 7. `typescript@latest` is 7.0.2, and openapi-typescript 7.13.0, the latest, cannot run on it (*Library behavior*). This spec pins TypeScript 6.0.3. Should a follow-up move to TypeScript 7 once openapi-typescript supports it? A possible route is TS 7 for `tsc` with openapi-typescript on a separate TypeScript 6 copy; that was not tried. *Recommendation*: stay on 6.0.3 for this spec, with no follow-up finding until openapi-typescript announces TS 7 support. This does not block approval.

## Verification

Filled by `qa-agent` during `/spec verify`.

| AC | Result | Evidence |
|---|---|---|
| AC-1 | Pass | `git ls-files frontend \| grep -E '\.py$\|pyproject\.toml$\|uv\.lock$'` -> no output. Evaluated against the index (Streamlit deletions are staged; `git ls-tree -r HEAD` still lists 11 such files because nothing is committed). `find frontend` (excluding node_modules) for `*.py`, `pyproject.toml`, `uv.lock` -> none in the working tree. |
| AC-2 | Pass | In `frontend/`: `npm ci` ok (0 vulnerabilities); `check:api`, `lint`, `typecheck`, `build` each exit 0; `npm test` 16 files, 90 passed, 0 failed; `test -f dist/index.html` -> ok; `grep -c '<html lang="es"' dist/index.html` -> 1. |
| AC-3 | Pass | `vitest --reporter=verbose`: all 7 `client.test.ts` cases pass (encodes `a%20b%3F%23c`, exact ingest/ask bodies with `k_results: 4`, `/api/health`, timeout -> `timeout`, non-2xx -> `http`, rejected fetch -> `network`). |
| AC-4 | Pass | `errors.test.ts` (400/422/404/413/500/504/timeout/network, `never includes the backend detail`) and `ask_view.test.tsx` error cases (422, 500, 504, timeout, network, 404 on the field) all pass. |
| AC-5 | Pass | `upload_view.test.tsx`: 15 tests pass (empty, whitespace, `/`, `.`, `..`, 1001 chars, no magic, over `MAX_PDF_BYTES`, exact limit accepted, 1000 chars sent trimmed, no file, 201/200/500/413 results). |
| AC-6 | Pass | `ask_view.test.tsx` (Enter/Shift+Enter, trim, rerank, validation, literal markup, `Página 3` no score, empty sources, null answer, 404, two answers in a polite live region) and `validation.test.ts` pass. Also exercised in the real browser (AC-10). |
| AC-7 | Pass | `status_dot.test.tsx`: checking -> online (200), offline on 503, timeout, network error; 4 passed. Live: header showed `Servidor en línea` on the deployed stack. |
| AC-8 | Pass | `docker build -t rag-docs-frontend:spec002 frontend` rc 0; `id -u` -> 101; `ExposedPorts` `{"8080/tcp":{},"8502/tcp":{}}` (grep count 1); `netstat -ltn` one LISTEN `0.0.0.0:8502`; `curl -sI /` -> 200 with nosniff, no-referrer, X-Frame-Options DENY, CSP; `/some/route` -> 1 `id="root"`; `/api/unknown` -> 404 with the same security headers. |
| AC-9 | Pass | `skaffold run -p local,chroma` rc 0 (frontend stabilized in 7 s, backend 62 s); readiness path `/`; via port-forward 8502: `/` -> 1 `id="root"`, `/api/health` -> healthy/connected, ingest of a 2,561,791-byte body -> 201 (not 413), encoded-title `/search` -> 200 with total_results 1, `/api/nope` -> 404. Ollama up (`embeddinggemma` present). |
| AC-10 | Pass | Playwright MCP on the deployed stack (screenshots `.playwright-mcp/ac10_*.png`, deleted from the repo after the run): 360/768/1280 x light/dark (`matchMedia` confirmed per combo): `scrollWidth == innerWidth` on `#upload` and `#ask` in all 6 combos; exactly 1 primary button per view; copy matches the Design table (Spanish, `lang="es"`); keyboard-only upload of `ros-intro.pdf`: Tab order nav, title, dropzone, Enter opens chooser, file set, Tab to Quitar then Subir PDF, Enter -> `qa ros intro indexado. Hacer una pregunta →`; visible focus (2px solid outline); console 0 messages (0 errors) after load, upload and ask; `Servidor en línea`. Caveats: title text entered with Playwright `fill` after focusing by Tab, file via the chooser tool; the first Tab after load landed on the title input (nav link order reached with Shift+Tab). Non-gating real ask on `qa ros intro`, question `What is ROS?` -> answer returned with `Fuentes (4)`. |
| AC-11 | Pass | `npm run dev -- --port 5173 --strictPort` with backend port-forwarded: `curl localhost:5173/api/health` -> healthy/connected; encoded `/search` through the proxy -> 200. |
| AC-12 | Pass | `uvx yamllint -d relaxed k8s skaffold.yaml` rc 0; `skaffold render -p local,chroma` frontend: `containerPort: 8502` (name `http`), Service port/targetPort 8502, probes `httpGet / port http`; `k8s/base/frontend/skaffold.yaml`: `port: 8502`, `localPort: 8502`; `docker-compose --env-file image.env --profile full -f docker-compose.yaml config --quiet` rc 0 (temp env files created from templates and removed; the `docker compose` plugin is not installed here, standalone `docker-compose` 5.2.0 used). |
| AC-13 | Pass | `actionlint` rc 0; `yamllint -d relaxed .github` rc 0 (line-length warnings only); npm-command grep -> 6; `npm run check:api` count 1; `backend/openapi.json` at line 44 under the `frontend:` filter; `frontend/uv.lock` -> no output. CI run itself not checked (non-gating; PR not opened). |
| AC-14 | Pass | Both greps (docs; `/front/` in CODEOWNERS) -> no output; `.github/CODEOWNERS` is `/frontend/`. |
| AC-15 | Pass | Biome 2.5.15; `lint` script `biome check --error-on-warnings .`; with the 5 probes lint exit 1 naming `useFilenamingConvention`, `noDefaultExport`, `noExplicitAny`, `noNonNullAssertion` (4 lines) and `src/format_probe.ts format` (1); probes removed -> lint exit 0; `@ts-*` grep -> no output; `find src -name '*[A-Z]*'` -> none. |
| AC-16 | Pass | `app.test.tsx` 4 tests pass, including `keeps session state across views and writes nothing to web storage` (datalist `['Manual A','Manual B']`, `#ask`, title prefilled `Manual B`). |
| AC-17 | Pass | Pins 6.0.3 / 7.13.0, overrides and both script strings exact; build-time scripts -> 0; header 1; biome exclusion 1; `types.ts` single import `import type { components } from './openapi_gen';`; no `interface`; `check:api` exit 0; snapshot test 1 passed. Note: `grep -c 'openapi-typescript\\|gen:api' Dockerfile` prints 1, expected 0: the only match is the comment on line 2 (`never runs gen:api`), no instruction runs it. Intent met; literal count differs. |
| AC-18 | Pass | `git status --short` before and after identical (52 lines, `diff` empty). Rename `page_content` -> `content_text`: snapshot test 1 failed, message names `export_openapi.py` and `npm run gen:api`; after export: 1 passed, `check:api` rc 1 (`Generated types are not up-to-date!`); after `gen:api`: `check:api` rc 0, `typecheck` rc 2 with errors naming `page_content` in `sources.tsx` (2), `sources.test.tsx` (3), `ask_view.test.tsx` (1); after `git checkout --` of `qa_response.py` (unchanged vs index beforehand) and regeneration, `cmp` of `openapi.json` and `openapi_gen.ts` against backups -> restored, model file cmp equal, `check:api` and `typecheck` rc 0. |

### Re-check 2026-10-17 (after the compose, `Makefile`, env-template removal)

Run by `qa-agent`. `git status --short` before and after: identical (63 lines, `diff` empty). Temp files only under a fresh `$TMPDIR` directory. A `skaffold dev -p local,chroma --port-forward` of the user's (pid 97784, started 23:58) was already running on this minikube, with the port-forwards on 8106, 8502, 8000 and 6024. `skaffold run`/`skaffold delete` would have replaced and then torn down that stack, so they were **not run**; AC-9 was checked against the running stack instead (see its row).

| AC | Result | Evidence (2026-10-17) |
|---|---|---|
| AC-1 | Pass | `git ls-files frontend \| grep -E '\.py$\|pyproject\.toml$\|uv\.lock$'` -> no output (rc 1). |
| AC-2 | Pass | `npm ci` ok (0 vulnerabilities); `check:api`, `lint`, `typecheck`, `build` each rc 0; `npm test` 16 files, 90 passed; `dist/index.html` ok; `grep -c '<html lang="es"'` -> 1. |
| AC-8 | Pass | `docker build -t rag-docs-frontend:spec002 frontend` rc 0; `id -u` -> 101; `ExposedPorts` `{"8080/tcp":{},"8502/tcp":{}}` (count 1); `netstat -ltn` one LISTEN `0.0.0.0:8502`; `/` -> 200 with nosniff, no-referrer, X-Frame-Options, CSP; `/some/route` -> 1 `id="root"`; `/api/unknown` -> 404 with nosniff, no-referrer, CSP. |
| AC-9 | Pass (deploy step not run) | `skaffold run`/`delete` skipped (see above). On the running stack: `kubectl rollout status` for chromadb, pgvector, rag-docs-backend, rag-docs-frontend -> all "successfully rolled out"; readiness path `/`; `skaffold render -p local,chroma` shows the frontend `containerPort: 8502`, `readinessProbe` and `livenessProbe`; via the 8502 port-forward: `/` -> 1 `id="root"`, `/api/health` -> healthy/connected, 2,561,791-byte ingest body -> 201 (not 413), encoded-title `/search` -> 200 `total_results: 1`. Side effect: the document `spec002 large ?#` now exists in that stack's databases. |
| AC-11 | Pass | `npm run dev -- --port 5173 --strictPort`; `curl localhost:5173/api/health` -> `{"status":"healthy","database":"connected"}`; the server was stopped afterwards. |
| AC-12 (as amended) | Pass | `uvx yamllint -d relaxed k8s skaffold.yaml` rc 0; `skaffold render -p local,chroma`: frontend `containerPort: 8502`, Service `port: 8502` / `targetPort: 8502` (name `http`); `k8s/base/frontend/skaffold.yaml`: `port: 8502`, `localPort: 8502`. No compose check (removed). |
| AC-13 | Pass | `actionlint` rc 0; `yamllint -d relaxed .github` rc 0; npm-command grep -> 6; `npm run check:api` count 1; `'backend/openapi.json'` at line 44 under `frontend:`; `frontend/uv.lock` -> no output. CI run not checked (non-gating). |
| AC-14 | Pass | Both greps -> no output. |
| AC-15 | Pass | Biome 2.5.15; lint script exact; with 5 probes lint rc 1 naming `useFilenamingConvention`, `noDefaultExport`, `noExplicitAny`, `noNonNullAssertion` and `src/format_probe.ts format`; probes removed -> lint rc 0 and `git status --short src` unchanged; `@ts-*` grep and `find src -name '*[A-Z]*'` -> no output. |
| AC-17 | Pass | Pins 6.0.3 / 7.13.0, `overrides`, both script strings exact; build-time script count 0; header 1; biome exclusion 1; `types.ts` single `import type { components } from './openapi_gen';`; no `interface`; `check:api` rc 0; snapshot test 1 passed. `grep -c 'openapi-typescript\|gen:api' Dockerfile` still prints 1 (the comment on line 2); no instruction runs it. |
| Backend gate | Pass (baseline) | `ruff check app tests`: only the two baseline errors (E501 `document_qa_steps.py:52`, F841 `document_service_test.py:155`); `ruff format --check .` 96 files formatted; `mypy app` no issues in 53 files; `pytest tests/unit` 155 passed. |
| (a) Removed-name grep | Pass | `grep -rniE 'docker-compose\|docker compose\|backend\.env\|env\.template\|image\.env\|frontend\.env\|Makefile'` over the repo, excluding `.git`, `node_modules`, `.venv`, `dist`, `resources`, lockfiles and `docs/specs`/`docs/findings` -> no output. Matches remain only in `docs/specs/` (SPEC-001, SPEC-002) and `docs/findings/` (F-019..F-022, README), all history. `Makefile`, `docker-compose.yaml`, `backend/backend.env.template`, `frontend/frontend.env.template` show as staged deletions. |
| (b) Env var names | Pass, 1 note | Every name in `backend/README.md` and `docs/guides/setup.md` is read: `Settings` fields in `config.py` (`LOCAL_LLM`, `USE_VERTEX_AI`, `OLLAMA_MODEL`, `OLLAMA_BASE_URL`, `OLLAMA_EMBEDDINGS_MODEL`, `VECTOR_DB_TYPE`, `CHROMADB_HOST/PORT`, `PGVECTOR_HOST/PORT/USER/PASSWORD/DATABASE`; `case_sensitive=False`), `USE_SECRETS`, `PROJECT_ID` and `OPENAI_API_KEY`/`COHERE_API_KEY` in `helpers.py`, `BACKEND_URL` in `tests/behave/environment.py:8`, `API_HOST`/`API_PORT`/`API_PROXY_TARGET` in the frontend config. No invented names (the old `CHROMA_HOST`, `CHROMA_PORT`, `DATABASE_URL` are gone). Note: `GOOGLE_APPLICATION_CREDENTIALS` (`setup.md:58`) is not read by repo code; it is the standard Google ADC variable consumed by the Vertex/Secret Manager client libraries, and the line is unchanged from `dev`. |
| (c) Diff review | Pass, nits | New changes are traceable to the 2026-10-17 changelog and N-5: deletions of the four files, `.gitignore` drops `!*.env.template`, docs rewritten for "no env files, Kubernetes only" (README, CLAUDE.md, backend/README.md, setup.md, k8s/README.md, architecture.md), findings F-019..F-022 annotated with unchanged statuses, agent files and `.claude/CLAUDE.md` ownership lines updated, qa-agent rule 7 and the k8s-agent equivalent added. No product code, API model, `Settings`, configmap or workflow change in them. Nits, no spec impact: `docs/guides/setup.md` states the configmap source for `API_HOST`/`API_PORT` twice in the "Frontend Configuration" section; the `.claude/CLAUDE.md` baseline heading says counts were updated 2026-10-16. |

Unchanged since the first verification, not re-run: AC-3 to AC-7, AC-10, AC-16 and AC-18. The frontend suite (90 passed) was re-run as part of AC-2; the backend and frontend source is untouched by these changes.

## Changelog

- 2026-10-16: Draft created.
- 2026-10-16: Amended with the user's answers to open questions 1–8 (9 stays open) and the new code-style requirement. **Alters requirements and contracts; needs user approval.** Requirements: Spanish copy table and `lang="es"` (REQ-7, *Design*); `<datalist>` title suggestions (REQ-3); Estándar/Rerank control with `k_results` fixed at 4 (REQ-3); per-title in-memory history split out as REQ-4; 20 MiB `MAX_PDF_BYTES`; port 8502 end to end (REQ-8, REQ-10); new REQ-12 (Google TypeScript Style Guide, Biome 2.5.15 config verified on a fixture tree); old REQ-4–REQ-10 renumbered to REQ-5–REQ-11 and old REQ-11 (docs) to REQ-13; 422 no longer shows backend field messages (they are English). Contracts: the port row is now non-breaking; new `frontend/biome.jsonc` code-style row; the CI lint gate runs with `--error-on-warnings`. ACs: Spanish text in AC-5/6/7/10; snake_case test paths; port 8502 in AC-8/9/12; new AC-15 (lint enforcement) and AC-16 (session state). Non-goals: document picker (F-033), `k` control, Playwright and mock mode, theme toggle. N-1 drops the Playwright ignore entries. F-028's follow-up split; F-033 recorded.
- 2026-10-16: Amended with the user's answer to open question 9, generated API types (option b). **Alters requirements and contracts; needs user re-approval.** Status stays Draft.
  - Requirements:
    - New REQ-14: the backend commits an offline OpenAPI snapshot, guarded by a unit test; the frontend generates `src/api/openapi_gen.ts` from it (`gen:api`, `check:api`), and `types.ts` only aliases it.
    - REQ-1 pins `typescript` 6.0.3 and `openapi-typescript` 7.13.0 exactly, with an `overrides` entry. TypeScript 7.0.2 crashes openapi-typescript, and installing without the override fails with ERESOLVE; both were executed.
    - REQ-11 adds `check:api` and triggers the frontend job on `backend/openapi.json`.
    - REQ-12's wire-types rule now points at the generated file.
    - REQ-13 adds the "Types (contract)" README section and the `contributing.md` workflow.
    - Non-goals now allow backend tooling, with no behavior change.
  - Contracts: new rows for the OpenAPI snapshot ↔ generated types and for the frontend toolchain pins; the CI row adds `check:api` and the `detect-changes` filter entry; the code-style row excludes the generated file in `biome.jsonc`; the gate-baseline row is updated.
  - Design: new § API types.
  - ACs: new AC-17 (wiring and pins) and AC-18 (drift in both directions, restored from backups); AC-2 and AC-13 extended.
  - Tasks: new backend-agent task T-7, which runs first; T-1, T-2, T-4, T-6 and N-2 updated.
  - Domains add backend. Open question 9 is closed, and open question 10 (TypeScript 7) is new and does not block approval.
- 2026-10-16: Approved by the user (open question 10: stay on TypeScript 6.0.3). Status → Approved.
- 2026-10-16: Amended after T-1's report of additions and deviations. The architect reviewed all eight against `frontend/src` and accepted them. The frontend gate was re-run on the branch: `check:api`, `lint`, `typecheck` exit 0, and vitest 90/90 passed. The snapshot test passed too. **Alters a requirement (REQ-3); needs user re-approval. No contract changes.** Status and task statuses are unchanged.
  - Requirements: REQ-3 now requires the Ask view to validate the title with REQ-2's rules and the question as non-empty before sending (`ask_view.tsx:69-77`, `validation.ts:15-27`). It is client-side only, and the titles it blocks cannot be reached by `/ask` anyway (*Context*).
  - ACs, in wording only:
    - AC-6 points its `k_results: 4` clause at AC-3(b). The view calls `api.ask(title, question, strategy)` (`client.ts:27`), so a view test cannot see the body.
    - AC-6 adds the Ask title and question validation, verified by `ask_view.test.tsx:70-79` and `validation.test.ts:6-23`.
    - AC-10 allows the product name "RAG Docs" and file sizes such as "1.4 MB" (`validation.ts:59-67`) as exceptions to "all copy Spanish".
  - Design § App:
    - The structure adds `src/validation.ts`, its test and `src/test/helpers.ts`.
    - The client takes plain arguments and builds the snake_case bodies inside `src/api/` (`client.ts:99-114`; REQ-12 allows snake_case only there).
    - A file is validated on pick and again at submit (`upload_view.tsx:39-65`).
    - A 404 on ask shows on the "Documento" field and a 413 on the file field.
    - `StatusDot` re-checks every 30 s (`status_dot.tsx:5,32`). REQ-6 and AC-7 are unaffected.
  - Copy table: adds "RAG Docs", "Principal", "Archivo PDF", "Quitar", the file size, "Estrategia", "Selecciona un archivo PDF.", the two loading texts and "Buscando respuesta…", and "Mostrar menos". The title validation rows now apply to Upload and Ask.
  - Design-skill overrides: the header has a minimum height and wraps (`app.module.css:9-18`).
  - Recorded, no spec change:
    - The five `biome-ignore` comments each carry a reason, as REQ-12 requires: `index.css:38,58,60` (`noImportantStyles`), `sources.tsx:51` (`noArrayIndexKey`) and `ask_view.tsx:64` (`useExhaustiveDependencies`).
    - T-1 ran the frontend half of AC-18 by temporarily editing `backend/openapi.json` instead of the model. That file is owned by backend-agent. It is untracked, so `git diff` cannot show the restore. The evidence that it was restored: the snapshot test passes and `check:api` exits 0. QA still runs AC-18 as written.
- 2026-10-16: User re-approved the REQ-3 amendment (Ask-view title and question validation) and the T-1 additions recorded above.
- 2026-10-16: Amended after the T-2 and T-4 reports. The architect built the image (`docker build`), ran it, and read `frontend/nginx/`, the Dockerfile, `k8s/base/frontend/` and `submission-check.yml`. **REQ-8 and the browser-facing routes contract change; needs user re-approval.** Everything else is wording, design or AC detail that matches the approved intent. Task statuses are unchanged.
  - Requirement and contract (re-approval): REQ-8 and the "Browser-facing routes" row now say that any other `/api/*` path returns 404 and is not proxied (`default.conf.template:36-39`). Before, REQ-8's "any other path that is not a file gets `index.html`" covered `/api/foo` too. The Vite dev proxy has no such route; REQ-9 only promises the two API routes.
  - **Open defect in T-2 (blocks AC-8 as amended):** `location /api/` does not include `security-headers.conf`, so its 404 carries none of REQ-8's headers (`curl -I /api/foo` against the built image, 2026-10-16). Every other route sends them. Fix: one `include /etc/nginx/security-headers.conf;` line in that location (k8s-agent).
  - AC-8, wording only: `ExposedPorts` must contain `8502/tcp` instead of equalling `{"8502/tcp":{}}`. The base image's `EXPOSE 8080` is inherited, and nothing listens on 8080 (`netstat -ltn` shows only `0.0.0.0:8502`). The AC-8 block adds that `netstat` check, so "listens on 8502" is still verified, and a `curl -sI /api/unknown` check for the 404 and its headers.
  - Design and contracts (no behavior change): `frontend/nginx/security-headers.conf` is added to *Design* § Serving, the image row and T-2's files. Every location must include it, because nginx does not inherit `add_header` into a location that sets its own. Today `/api/` does not; see the defect above. The template has no server-level `add_header`. Also recorded: `Cache-Control: no-cache` on `/` and the actual base image tag, `1.29-alpine`.
  - *Library behavior*: an unresolvable `API_HOST` stopping nginx at start is now executed, not inferred (`[emerg] host not found in upstream`). The "Frontend env" contract row is updated to match.
  - Not deviations, recorded for QA:
    - `frontend/frontend.env.template` (`API_HOST=localhost`, `API_PORT=8106`) is what *Design* § Compose and the "Frontend env" row already specified.
    - The workflow-level `concurrency` group is required by T-4 ("Add `concurrency` if absent"). The CI contract row now names it.
    - The frontend CI job is renamed `check-format-frontend` → `frontend-checks`. The contract row now names it. The main session reported that `dev` has no required status checks; the architect did not check this. AC-13 does not depend on the job name.
- 2026-10-16: User re-approved REQ-8 / Browser-facing routes amendment (unknown `/api/*` → 404 with security headers). T-2 reopened for the missing header include on `location /api/`.
- 2026-10-16: T-2 defect fixed: `location /api/` now includes `security-headers.conf` (`default.conf.template:38`); the 404 carries all security headers. All tasks Done; Status → In review.
- 2026-10-16: T-6 verification by qa-agent: AC-1 to AC-18 all Pass (AC-13 CI run non-gating, not checked). Status -> Done; F-028 and F-029 -> Fixed (SPEC-002). For the architect: the AC-17 Dockerfile grep counts 1 because of a comment, not an instruction.
- 2026-10-17: User-directed change after verification: the frontend has no env file. **Alters the "Frontend env" contract row (sources only; keys and values unchanged). No requirement changes. The change was directed by the user.** Status stays Done.
  - `frontend/frontend.env.template` is removed. Kubernetes reads `API_HOST`/`API_PORT` from `k8s/base/frontend/configmap.yaml`; compose sets them inline (`environment:` `API_HOST=localhost`, `API_PORT=8106`) instead of `env_file: frontend/frontend.env`; the Vite dev proxy uses `API_PROXY_TARGET` (`frontend/vite.config.ts:5`).
  - Updated: the "Frontend env" contract row, *Design* § Compose, the AC-12 command block comment (only `backend/backend.env` is copied from a template) and T-2's text and files. *Context* (pre-spec state on `dev` @ `1fbb820`), the AC-12 *Verification* evidence and the 2026-10-16 changelog lines are history and are left as they were.
  - k8s-agent removes the template and updates `docker-compose.yaml`, `docs/guides/setup.md` and `k8s/README.md`, and re-runs AC-12's compose check (`docker compose --env-file image.env --profile full -f docker-compose.yaml config --quiet` -> exit 0) against the new compose file. The architect updated `docs/reference/architecture.md` § Frontend and the root `CLAUDE.md` Configuration section.
- 2026-10-17: Scope extension after verification, relayed by the main session as a user decision: Docker Compose is dropped. **Alters REQ-10, AC-12 and the contracts (a run path is removed); needs user re-approval.** Status stays Done.
  - Removed: `docker-compose.yaml` and `backend/backend.env.template` (k8s-agent, T-2) and the root `Makefile`, which only wrapped `docker compose` (main session, new note N-5). Kubernetes via Skaffold + minikube is the only way to run the stack. The backend reads process environment variables plus the defaults in `config.py`; it sets no `env_file` (`config.py:92-96`; pydantic-settings 2.6.0 defaults `env_file` to `None`, checked in the installed package). Kubernetes supplies the variables through the `backend-config` configmap and the `api-keys` secret (`k8s/base/backend/deployment.yaml:27-31`).
  - Updated: Goals (Kubernetes is the only run path) and Non-goals (no replacement for compose or `make`); REQ-10 drops the `docker compose --profile full` sentence; contracts: the `Settings` row no longer names `backend.env.template`, the "Frontend env" row drops the compose source, the port row drops the compose host port, and a new row records the removal (breaking: run path), with one migration sentence; *Design* § Serving, Compose; AC-12's text and command block drop the compose check; T-2's text and files.
  - Left as history: *Context* (pre-spec state on `dev` @ `1fbb820`), open question 3, the AC-12 *Verification* evidence (qa-agent's, run against the compose file that existed then) and the earlier changelog lines.
  - Superseded: the previous 2026-10-17 entry's instruction that k8s-agent re-runs AC-12's compose check. There is no compose file to check. AC-12 now covers yamllint, `skaffold render` and the port-forward, a subset of what the AC-12 *Verification* already passed.
  - Findings F-019, F-020 and F-021 cited the removed template; each gets a dated note and annotated or narrowed evidence. F-022 gets a note. No finding status changes.
- 2026-10-17: User directed and approved dropping Docker Compose, `Makefile` and `backend/backend.env.template` ("lets drop the compose entirely").
- 2026-10-17: qa-agent re-check after the compose, `Makefile` and env-template removal: AC-1, AC-2, AC-8, AC-9 (deploy step not run, a user `skaffold dev` was running; checked against it), AC-11 to AC-15, AC-17, the backend gate, the removed-names grep, the env-var-name check and the diff review all pass. Status stays Done.
