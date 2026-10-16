# F-032: Leftover `pdb` breakpoints in `backend/admin_chroma.py`

| Field | Value |
|---|---|
| Severity | Low |
| Category | maintenance |
| Status | Open |
| Verification | Confirmed. Checked by the architect on 2026-10-15 in the SPEC-001 working tree. `grep` found `import pdb` and two `pdb.set_trace()` calls (lines below). ruff 0.14.3, the version pinned in `backend/pyproject.toml:62`, gave these results: `ruff check --select T10 .` from `backend/` reports exactly these 3 T100 hits backend-wide. The repo's own rule set reports `admin_chroma.py` clean. Frontend `--select T10` is clean. A minimal `pdb.set_trace()` snippet run with the backend venv Python 3.10.20 and stdin at EOF raised `bdb.BdbQuit` and exited 1. `grep` and `codegraph_explore` found no imports of the script and no runner in `k8s/`, `skaffold.yaml` or `.github/`. Not done: `admin_chroma.py` itself was not run against a live Chroma. The interactive TTY behavior assumes standard `pdb`. |
| Tracking issue | — |
| Found | 2026-10-15. Reported by `qa-agent` during SPEC-001 verification (out of its scope). Introduced in `a802a24` (#10, 2025-12-08). |

## Problem

`backend/admin_chroma.py` is the manual ChromaDB setup script. It still contains debugging breakpoints:

- `import pdb` at the top.
- `pdb.set_trace()` after the tenant and database are created and checked.
- `pdb.set_trace()` after the collection is created.

Running the documented setup command (`python admin_chroma.py`) stops at a `(Pdb)` prompt twice. Without a TTY, for example in a script or with stdin redirected, the first breakpoint reads EOF, raises `bdb.BdbQuit` and exits with status 1. That happens before the collection is created.

No lint gate catches it. The ruff rule set does not include the `flake8-debugger` rules (T10). CI runs no `ruff check`. The gate command `ruff check app tests` does not cover scripts at the backend root.

## Evidence

Lines are cited in the SPEC-001 working tree. On `dev` @ `200c4cf` they were 3, 53 and 66. SPEC-001 T-4 changed the `create_collection` call at `admin_chroma.py:64-66` to pass cosine metadata, and that edit shifts the last breakpoint by +2.

- `backend/admin_chroma.py:3`: `import pdb`.
- `backend/admin_chroma.py:36-46`: creates the tenant `dev` and the database `rag-database`, before the first breakpoint.
- `backend/admin_chroma.py:53`: `pdb.set_trace()`.
- `backend/admin_chroma.py:64-66`: `create_collection(name=collection_name, metadata={"hnsw:space": "cosine"})`, after the first breakpoint.
- `backend/admin_chroma.py:68`: `pdb.set_trace()`.

**Not shipped in the image.**

- `backend/Dockerfile` copies only `app`, `main.py` and `alembic.ini` into the runtime stage.
- `k8s/base/backend/skaffold.yaml:15-17`: the build context is `backend/` with that Dockerfile.
- `backend/.dockerignore` does not list `admin_chroma.py`. The script is excluded only by the explicit `COPY` lines.

**Not run by anything automated.**

- No Python module imports it.
- Nothing in `k8s/`, `skaffold.yaml` or `.github/workflows/` runs it.
- In the cluster, `k8s/base/vectordb/chroma/entrypoint.sh:14-23` creates the tenant and database with `curl`.
- The backend creates the cosine collection itself in `ChromaDBClient.get_or_create_collection` (`backend/app/infrastructure/vector_db/chroma_client.py:53-61`).

**Documented as a manual setup step.**

- `backend/README.md:36,279`.
- `docs/guides/setup.md:97-101`.
- `docs/reference/architecture.md:93` ("Requires: `admin_chroma.py` to initialize tenant/database on first run").
- `docs/reference/architecture.md:195` also names the script as one of the places that create the cosine collection.

**Not caught by lint.**

- `backend/pyproject.toml:77-83`: `[tool.ruff.lint] select` is `E`, `W`, `F`, `I`, with no `T10`. The frontend is the same (`frontend/pyproject.toml:28-34`).
- With that rule set, `ruff check admin_chroma.py` passes. `F401` does not fire on `import pdb`, because the module is used.
- `.github/workflows/submission-check.yml:68` runs only `ruff format --check .`, never `ruff check`. This is already tracked in [F-016](F-016-ci-gaps.md).
- The gate baseline in `.claude/CLAUDE.md` uses `ruff check app tests`, which excludes backend-root scripts such as `admin_chroma.py`. Enabling T10 alone would not catch this file unless the lint path covers `.`.

**Reproduction.**

- `uvx ruff@0.14.3 check --select T10 .` (from `backend/`):
  - `admin_chroma.py:3:1: T100 Import for pdb found`
  - `admin_chroma.py:53:1: T100 Trace found: pdb.set_trace used`
  - `admin_chroma.py:68:1: T100 Trace found: pdb.set_trace used`
- `uvx ruff@0.14.3 check --extend-select T10 .` (from `backend/`) reports those 3 hits plus the 2 known baseline errors (E501, F841). There are no other new hits.
- A `python -I -c "import pdb; pdb.set_trace()" < /dev/null` equivalent with the backend venv Python 3.10.20 printed `(Pdb)`, raised `bdb.BdbQuit` and exited 1.

## Impact

- **Interactive run** (the documented path): the script pauses twice at `(Pdb)`. The operator has to type `c` to continue. Nothing explains the prompt.
- **Non-interactive run**: the script exits 1 at line 53. The tenant and database already exist at that point, but the cosine collection from line 64 is never created. A wrapper that checks the exit status reports the setup as failed.
- **Reach is limited:**
  - The script is not in the backend image and is not run in Kubernetes or CI.
  - The tenant and database are created by `entrypoint.sh` in the cluster.
  - The collection is created with cosine metadata by the backend on first use (`chroma_client.py:53-61`).
- No production or data-correctness effect.

## Severity rationale

Low (hygiene). The breakpoints affect only a manual, local-only setup script, and the app does not depend on it to reach a correct state. The aborted non-interactive run is the one functional effect, and it is reachable only off the documented interactive path. Raise to Medium if the script is ever wired into automation, such as a k8s Job, CI or an init container.

## Suggested fix

1. **backend-agent**: delete `import pdb` and both `pdb.set_trace()` calls in `backend/admin_chroma.py`.
2. **backend-agent**, optional: add `"T10"` (flake8-debugger) to `[tool.ruff.lint] select` in `backend/pyproject.toml`, and the same in `frontend/pyproject.toml`, so `ruff check` flags `pdb`/`breakpoint()`. Verified to add no new hits beyond this file in either package.
3. The lint rule only helps where `ruff check` runs over the script:
   - CI: see F-016 (ci-agent).
   - The `.claude/CLAUDE.md` gate command: it would need to lint `.` (or include `admin_chroma.py`), not only `app tests`.

## Follow-up

- [ ] Remove the three `pdb` lines from `backend/admin_chroma.py`
- [ ] Decide whether to enable ruff `T10` in `backend/pyproject.toml` and `frontend/pyproject.toml`
- [ ] Decide whether the gate command in `.claude/CLAUDE.md` should lint backend-root scripts (`ruff check .`). This needs a user decision, because that file is outside architect scope.
- [ ] `ruff check` in CI (tracked in [F-016](F-016-ci-gaps.md))
- [ ] Decide where the fix lands:
  - SPEC-001 T-4 already owns `backend/admin_chroma.py` and is marked Done. Folding it in would amend SPEC-001.
  - A separate small spec, or a direct hygiene PR, would keep SPEC-001 unchanged.
  - This is the user's decision.
