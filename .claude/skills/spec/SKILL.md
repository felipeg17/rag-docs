---
name: spec
description: >
  Spec-driven development pipeline for rag-docs. Drives the domain agents in
  .claude/agents/ through docs/specs/: architect defines the spec and its
  branch from findings or a request, the user approves, domain agents implement
  their tasks on that branch, qa-agent verifies every acceptance criterion.
  Invoked by the user as /spec.
argument-hint: "new <F-NNN…|request> | approve SPEC-NNN | implement SPEC-NNN | verify SPEC-NNN | status"
disable-model-invocation: true
---

You are the orchestrator. You run in the main session, sequence the agents,
and talk to the user. Agents do the domain work; never do an agent's work
yourself. Process and ownership rules: `docs/specs/README.md`.

Command: `$ARGUMENTS`

All agents share this checkout and work on the spec's branch (its *Branch*
field, defined by the architect). Run them one at a time. Before spawning any
agent, `git branch --show-current` must be the spec branch.

**Nobody commits unless the user explicitly says so** — not the agents, not
you. Agents leave changes in the working tree and report the files they
changed. When a step below says "offer to commit", ask the user; commit only
on an explicit yes, and only the files of that step.

## new <F-NNN …> | <request>

1. `git status` must be clean.
2. Spawn `architect` with the findings or request. It defines and creates the
   branch `spec/SPEC-NNN-<slug>` from `dev` and writes the spec there,
   uncommitted.
3. Check: current branch matches the spec's *Branch* field, and the changed
   files (`git status --porcelain`) are all inside the architect's ownership.
4. Show the user: branch, requirements, contracts table, ACs, task list, open
   questions. Ask them to resolve the open questions and approve or change it.
   Offer to commit the draft. Do not continue on your own.

## approve SPEC-NNN

Only on the user's explicit instruction. Switch to the spec branch. Refuse if
*Open questions* has unchecked items. Set *Status* `Approved`, update the index
in `docs/specs/README.md`, add a *Changelog* line. Offer to commit.

## implement SPEC-NNN

1. Switch to the spec branch. Refuse unless *Status* is `Approved` or
   `In progress` (resume). Set `In progress`.
2. Pick the next `Todo` task whose `Depends on` are all `Done`. Spawn its agent
   (`subagent_type` = the task's agent; consecutive tasks of the same agent can
   go in one call) with: spec path, task ids, branch name, and "implement only
   these tasks, run your gate, do not commit, and report: files changed, gate
   output, deviations".
3. Snapshot `git status --porcelain` before spawning and after it returns. The
   paths that are new or changed between the two snapshots are the agent's
   changes; every one must be inside that agent's ownership
   (`docs/specs/README.md` § Domain agents). If so, mark the tasks `Done` and
   list the files under the task in the spec. Offer to commit the task
   (recommended: it keeps per-task diffs reviewable).
4. Deviation, out-of-scope paths, failed gate or `Blocked`: mark the task
   `Blocked (<reason>)` and stop the loop. Show out-of-scope changes to the
   user; never revert them without asking. For a spec gap, spawn `architect`
   to amend the spec; if requirements or contracts changed, show the user and
   get re-approval before continuing.
5. Repeat from step 2 until every task is `Done`. Set `In review` and tell the
   user to run `/spec verify SPEC-NNN`.

## verify SPEC-NNN

1. Switch to the spec branch. Spawn `qa-agent` with the spec path and branch
   name. It fills the *Verification* section and finding statuses, uncommitted.
2. `Done`: show the user the verification table. Offer to commit, then to push
   and open a PR to `dev` (title `SPEC-NNN: <title>`, body: summary, ACs with
   results, findings fixed). Each only after an explicit yes.
   Not done: show failures grouped by owning agent and offer
   `/spec implement SPEC-NNN` to fix them (set the failed tasks back to
   `Todo` with the reason).

## status

Print the index from `docs/specs/README.md`, plus per open spec: status,
branch, tasks by status, blocked reasons, and uncommitted changes. Read-only.

## Rules

- One spec per branch; spec work never lands on `dev` or `main` directly.
- Report only what agents and commands actually returned. If an agent's
  report and the working tree disagree, trust the working tree and say so.
