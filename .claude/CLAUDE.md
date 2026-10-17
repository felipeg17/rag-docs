<!-- CODEGRAPH_START -->
# CodeGraph

In repositories indexed by CodeGraph (a `.codegraph/` directory exists at the repo root), reach for it BEFORE grep/find or reading files when you need to understand or locate code:

- **MCP tool** (when available): `codegraph_explore` answers most code questions in one call — the relevant symbols' verbatim source plus the call paths between them, including dynamic-dispatch hops grep can't follow. Name a file or symbol in the query to read its current line-numbered source. If it's listed but deferred, load it by name via tool search.
- **Shell** (always works): `codegraph explore "<symbol names or question>"` prints the same output.

If there is no `.codegraph/` directory, skip CodeGraph entirely — indexing is the user's decision.
<!-- CODEGRAPH_END -->

# Software factory (spec-driven development)

Product changes go through specs: `docs/specs/README.md` (lifecycle, ownership), template
`docs/specs/TEMPLATE.md`, driven by the `/spec` skill (`.claude/skills/spec/`).

## Agents (`.claude/agents/`)

| Agent | Model | Role |
|---|---|---|
| `architect` | opus | specs and their branches, findings triage, `docs/reference/` |
| `backend-agent` | sonnet | `backend/` |
| `frontend-agent` | sonnet | `frontend/` |
| `k8s-agent` | sonnet | `k8s/`, Skaffold, Dockerfiles, `frontend/nginx/`, `docs/guides/` |
| `ci-agent` | sonnet | `.github/`, `docs/development/` |
| `qa-agent` | sonnet | AC verification, behave suite, closes specs |

- All agents work in the same checkout on the branch the architect defines for the spec
  (`spec/SPEC-NNN-<slug>`), one agent at a time, each changing only its own files.
- Nobody commits (agents or main session) unless the user explicitly says so.
- Agents cannot spawn agents; the main session orchestrates them through `/spec`.

## Gate baseline (`dev` @ 83304a4, 2026-10-15; frontend and backend counts updated by SPEC-002, 2026-10-16)

Pre-existing errors. Gates fail only on errors beyond these; remove an entry when it is fixed.

- Backend `ruff check app tests`: E501 `tests/behave/steps/document_qa_steps.py:52`, F841
  `tests/unit/services/persistence/document_service_test.py:155`. `ruff format --check`, `mypy app`
  clean; `pytest tests/unit`: 155 passed (includes the OpenAPI snapshot test). After an API model or
  route change: `uv run python export_openapi.py` (from `backend/`), then `npm run gen:api` in
  `frontend/`.
- Frontend (from `frontend/`, after `npm ci`): `npm run check:api`, `npm run lint`,
  `npm run typecheck`, `npm test` (90 passed), `npm run build`: all clean.
- `uvx yamllint -d relaxed k8s skaffold.yaml` and `uvx --from actionlint-py actionlint`: clean.
- `skaffold render` needs a running minikube.
