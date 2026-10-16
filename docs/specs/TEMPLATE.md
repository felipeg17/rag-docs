# SPEC-NNN: <title>

| Field | Value |
|---|---|
| Status | Draft |
| Findings | F-NNN, … (or —) |
| Issue | #NN (or —) |
| Domains | backend, frontend, k8s, ci, qa |
| Branch | `spec/SPEC-NNN-<slug>` |
| Base | `dev` @ `<sha>` |

## Context

What is wrong or missing today, with evidence (`file:line`). Link the findings.

## Goals

- …

## Non-goals

- … (explicitly out of scope, to stop scope creep)

## Requirements

- **REQ-1**: The system shall …
- **REQ-2**: When <trigger>, the system shall …

## Contracts

List every interface this spec changes. Write `None` if a category is untouched.

| Contract | Before | After | Breaking? |
|---|---|---|---|
| API models (`backend/app/models/`) | | | |
| HTTP routes / status codes | | | |
| `Settings` ↔ configmaps ↔ `backend.env.template` | | | |
| DB schema / Alembic migration | | | |
| Vector DB metadata / collection / table | | | |
| Prompts (`backend/app/prompts/`) | | | |
| CI jobs / gates | | | |

## Design

How it will be built: components touched, data flow, alternatives considered and why rejected.

## Acceptance criteria

| ID | Given / When / Then | Verified by |
|---|---|---|
| AC-1 | Given …, when …, then … | `backend/tests/unit/…::test_…` |
| AC-2 | … | `behave backend/tests/behave/….feature` |
| AC-3 | … | `<command>` → `<expected output>` |

## Tasks

| ID | Task | Agent | Depends on | Files | Status |
|---|---|---|---|---|---|
| T-1 | … | backend-agent | — | `backend/app/…` | Todo |
| T-2 | … | qa-agent | T-1 | `backend/tests/behave/…` | Todo |

Status: `Todo` · `Doing` · `Done` · `Blocked (<reason>)`.

## Open questions

- [ ] … (must be empty before `Approved`)

## Verification

Filled by `qa-agent` during `/spec verify`.

| AC | Result | Evidence |
|---|---|---|
| AC-1 | | |

## Changelog

- YYYY-MM-DD: Draft created.
