# Specs

Spec-driven development: every change to product code starts from an approved spec. A spec turns a
finding (`docs/findings/F-NNN`) or a feature request into requirements, contracts, acceptance
criteria and a task breakdown per domain agent.

## Lifecycle

```
finding / request
      ↓  /spec new
architect   → SPEC-NNN (Draft)
      ↓  user review → Approved          ← nothing is implemented before this
      ↓  /spec implement
agents      → tasks on branch spec/SPEC-NNN-<slug> (In progress)
      ↓  /spec verify
qa          → every AC checked (In review → Done, or back to In progress)
      ↓
PR to dev; findings → Fixed
```

| Status | Meaning | Who sets it |
|---|---|---|
| `Draft` | Written by the architect, open questions allowed | architect |
| `Approved` | User accepted it; open questions resolved | user (via main session) |
| `In progress` | At least one task started | main session |
| `In review` | All tasks done; QA verifying | main session |
| `Done` | Every acceptance criterion passed | qa |
| `Rejected` | Not doing it; reason recorded | user |

## Rules

1. **Spec is the source of truth.** Engineers implement only the tasks assigned to their domain.
   Anything the spec does not cover is a deviation: stop and report it; the architect amends the
   spec (Changelog) and the user re-approves if requirements or contracts change.
2. **Contracts are explicit.** Every change to an API model, `Settings` field, configmap key,
   DB schema/migration, prompt or CI job is listed under *Contracts* with before/after.
3. **Acceptance criteria are testable.** Each `AC-N` names how it is verified: a unit test path, a
   behave scenario, or a command with expected output.
4. **Tasks are single-domain.** One task = one domain agent = files inside that agent's ownership.
   Cross-domain work is split into tasks with explicit `Depends on`.
5. **Ids are permanent.** Next free `SPEC-NNN`; never reuse.

## Domain agents

Defined in `.claude/agents/`. Ownership is exclusive: an agent edits only its paths.

| Agent | Model | Owns |
|---|---|---|
| `architect` | opus | spec branch, `docs/specs/`, `docs/findings/`, `docs/reference/`, `docs/README.md`, root `README.md` and `CLAUDE.md` |
| `backend-agent` | sonnet | `backend/` (except `Dockerfile`, `tests/behave/`) |
| `frontend-agent` | sonnet | `frontend/` (except `Dockerfile`) |
| `k8s-agent` | sonnet | `k8s/`, `skaffold.yaml`, `docker-compose.yaml`, all `Dockerfile`s, `*.env.template`, `docs/guides/` |
| `ci-agent` | sonnet | `.github/`, `docs/development/` |
| `qa-agent` | sonnet | `backend/tests/behave/`, spec *Verification*, finding *Status* |

All agents work on the branch the architect defines for the spec (`spec/SPEC-NNN-<slug>`, from
`dev`), one at a time, each committing only the files of its own tasks. No agent spawns other
agents: orchestration lives in the `/spec` skill.

## Index

| ID | Title | Status | Findings | Branch |
|---|---|---|---|---|
| [SPEC-001](SPEC-001-scope-retrieval-to-document.md) | Scope retrieval to the requested document | Draft | F-001 | `spec/SPEC-001-scope-retrieval-to-document` |
