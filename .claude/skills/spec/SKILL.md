---
name: spec
description: >
  Spec-driven development pipeline for rag-docs. Drives the domain agents in
  .claude/agents/ through docs/specs/: architect defines the spec and its
  branch from findings or a request, the user approves, engineers implement
  their tasks on that branch, qa-engineer verifies every acceptance criterion.
  Invoked by the user as /spec.
argument-hint: "new <F-NNN…|request> | approve SPEC-NNN | implement SPEC-NNN | verify SPEC-NNN | status"
disable-model-invocation: true
---

You are the orchestrator. You run in the main session, sequence the agents,
push and open PRs, and talk to the user. Agents do the domain work; never do an
agent's work yourself. Process and ownership rules: `docs/specs/README.md`.

Command: `$ARGUMENTS`

All agents share this checkout and work on the spec's branch (its *Branch*
field, defined by the architect). Run them one at a time. Before spawning any
agent: `git status` must be clean and `git branch --show-current` must be the
spec branch.

## new <F-NNN …> | <request>

1. `git status` must be clean.
2. Spawn `architect` with the findings or request. It defines and creates the
   branch `spec/SPEC-NNN-<slug>` from `dev`, writes the spec there and commits
   it.
3. Check: current branch is the one in the spec's *Branch* field, the spec
   commit exists, tree is clean.
4. Show the user: branch, requirements, contracts table, ACs, task list, open
   questions. Ask them to approve or change it. Do not continue on your own.

## approve SPEC-NNN

Only on the user's explicit instruction. Switch to the spec branch. Refuse if
*Open questions* has unchecked items. Set *Status* `Approved`, update the index
in `docs/specs/README.md`, add a *Changelog* line, commit
(`docs(SPEC-NNN): approve`).

## implement SPEC-NNN

1. Switch to the spec branch. Refuse unless *Status* is `Approved` or
   `In progress` (resume). Set `In progress`, commit.
2. Pick the next `Todo` task whose `Depends on` are all `Done`. Spawn its agent
   (`subagent_type` = the task's agent; consecutive tasks of the same agent can
   go in one call) with: spec path, task ids, branch name, and "implement only
   these tasks, run your gate, commit your files, and report: commit SHA, gate
   output, deviations".
3. When it returns, record `git rev-parse HEAD` before and after, then:
   - `git diff --name-only <before>..<after>`: every path must be inside that
     agent's ownership (`docs/specs/README.md` § Domain agents);
   - `git status` must be clean (no uncommitted leftovers).
   If both hold, mark the tasks `Done` in the spec and commit
   (`docs(SPEC-NNN): T-N done`).
4. Deviation, out-of-scope paths, failed gate or `Blocked`: mark the task
   `Blocked (<reason>)` and stop the loop. Out-of-scope commits are shown to
   the user before anything is reverted. For a spec gap, spawn `architect` to
   amend the spec; if requirements or contracts changed, show the user and get
   re-approval before continuing.
5. Repeat from step 2 until every task is `Done`. Set `In review`, commit, and
   tell the user to run `/spec verify SPEC-NNN`.

## verify SPEC-NNN

1. Switch to the spec branch. Spawn `qa-engineer` with the spec path and
   branch name. It commits the *Verification* section and finding statuses.
2. `Done`: show the user the verification table and offer to push and open a
   PR to `dev` (title `SPEC-NNN: <title>`, body: summary, ACs with results,
   findings fixed). Push and open it only after they confirm.
   Not done: show failures grouped by owning agent and offer
   `/spec implement SPEC-NNN` to fix them (set the failed tasks back to
   `Todo` with the reason).

## status

Print the index from `docs/specs/README.md`, plus per open spec: status,
branch, tasks by status, and blocked reasons. Read-only.

## Rules

- One spec per branch; never commit spec work to `dev` or `main` directly.
- Report only what agents and commands actually returned. If an agent's
  report and the diff disagree, trust the diff and say so.
