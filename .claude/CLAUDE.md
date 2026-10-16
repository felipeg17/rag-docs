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

| Agent | Model | Isolation | Role |
|---|---|---|---|
| `architect` | opus | main checkout | specs, findings triage, `docs/reference/` |
| `backend-engineer` | sonnet | worktree | `backend/` |
| `frontend-engineer` | sonnet | worktree | `frontend/` |
| `k8s-engineer` | sonnet | worktree | `k8s/`, Skaffold, Dockerfiles, docker-compose, env templates, `docs/guides/` |
| `ci-engineer` | sonnet | worktree | `.github/`, `docs/development/` |
| `qa-engineer` | sonnet | main checkout | AC verification, behave suite, closes specs |

- Agents cannot spawn agents; the main session orchestrates, owns git and merges worktree branches
  into `spec/SPEC-NNN-<slug>`.
- Worktrees branch from `main`, not the current HEAD: always pass the spec branch name so the agent
  syncs to it first.
- Agent commits carry `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.

## Gate baseline (`dev` @ 83304a4, 2026-10-15)

Pre-existing errors. Gates fail only on errors beyond these; remove an entry when it is fixed.

- Backend `ruff check app tests`: E501 `tests/behave/steps/document_qa_steps.py:52`, F841
  `tests/unit/services/persistence/document_service_test.py:155`. `ruff format --check`, `mypy app`
  clean; `pytest tests/unit`: 130 passed.
- Frontend `ruff check .`: I001 `components/__init__.py:1`. `mypy .` clean.
- `uvx yamllint -d relaxed k8s skaffold.yaml` and `uvx --from actionlint-py actionlint`: clean.
- `skaffold render` needs a running minikube.
