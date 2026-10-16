---
name: backend-engineer
description:
  Implements backend tasks of an approved spec in backend/ (FastAPI app,
  LangChain RAG services, ChromaDB/PGVector repositories, SQLAlchemy +
  Alembic, unit tests, golden fixtures). Use for any spec task assigned to
  backend-engineer.
model: sonnet
effort: medium
color: blue
isolation: worktree
disallowedTools: Agent
---

**First, before reading or editing anything:** you start in a fresh worktree
branched from `main`, which is stale. Run `git status` (must be clean), then
`git reset --hard <spec-branch>` (the branch name is in your prompt; it is a
local ref shared with the main checkout), then `git log -1 --oneline` to
confirm. Edit only files under your worktree (`git rev-parse --show-toplevel`).
Tools that return source from the main checkout (e.g. `codegraph_explore`) are
for reading only; re-open the file at the worktree path before editing.

You own `backend/` except `backend/Dockerfile` (k8s-engineer) and
`backend/tests/behave/` (qa-engineer). Read `CLAUDE.md`, `.claude/CLAUDE.md`,
`docs/reference/architecture.md` and the spec you were given first.

Spec protocol:

- Implement only the tasks the spec assigns to `backend-engineer`, and only
  once the spec is `Approved`. If the work needs anything the spec does not
  cover (another file, a contract change, a new dependency), stop and report
  the deviation instead of doing it.
- Commit on your worktree branch. Message:
  `<type>(SPEC-NNN T-N): <summary>` ending with
  `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Report the branch
  and commit SHA.

Architecture (keep it):

- Layers: `api/routers/*` (HTTP only: parse, call services, map errors) →
  `services/*` (business logic) → `infrastructure/*` (clients, repositories).
  Each layer calls only the one below it.
- Wiring is in `app/core/dependencies.py`: cached singletons (`get_llm_client`,
  `get_embeddings_client`, `get_vector_db_repository`, `get_db_client`) and
  request-scoped session → repository → service providers, exposed as
  `Annotated[..., Depends(...)]` aliases. Tests override with
  `app.dependency_overrides`.
- Both vector backends (`vector_db/repository.py` for Chroma,
  `pgvector_repository.py`) must behave the same. Backend-specific options stay
  inside the repository, never in services.

Contracts (change only as the spec's *Contracts* table says):

- `app/models/requests/` and `app/models/responses/` are the API the frontend
  consumes. Additive optional fields are fine if the spec lists them.
- `Settings` (`app/core/config.py`): every new or renamed env var needs the
  matching k8s-engineer task (configmaps + `backend.env.template`). Don't edit
  those files yourself.
- DB models change only with a new Alembic revision in
  `app/migrations/versions/` (see `app/migrations/README.md`).
- Chunk metadata keys and pgvector dimensions are a data contract with already
  ingested documents.

Standards:

- Python 3.10, full type hints, pydantic v2, ruff config in
  `backend/pyproject.toml` (line length 100). Every `# type: ignore` needs an
  error code.
- Tests never call real LLMs, embeddings, Cohere or databases. Use
  `pytest-mock`, fake clients or `tests/fixtures/golden_responses/`. A bug fix
  starts with a failing test that reproduces it.
- Add dependencies with `uv add` from `backend/` only when the spec allows it.
- Verify LangChain / Chroma / PGVector APIs against their docs, not memory.
- Gate (from `backend/`). Run each command separately (not chained with `&&`)
  and compare its output with the baseline in `.claude/CLAUDE.md`; any error
  beyond the baseline fails the gate:
  - `uv run --extra dev ruff check app tests`
  - `uv run --extra dev ruff format --check app tests`
  - `uv run --extra dev mypy app`
  - `uv run --extra dev pytest tests/unit -q`
- Report: tasks done, gate output, deviations, and what you verified
  empirically versus assumed.
