---
name: spec
description: >
  Spec-driven development pipeline for rag-docs. Drives the domain agents in
  .claude/agents/ through docs/specs/: architect drafts a spec from findings or
  a request, the user approves, engineers implement their tasks in worktrees,
  qa-engineer verifies every acceptance criterion. Invoked by the user as
  /spec.
argument-hint: "new <F-NNN…|request> | approve SPEC-NNN | implement SPEC-NNN | verify SPEC-NNN | status"
disable-model-invocation: true
---

You are the orchestrator. You run in the main session, own git (branches,
merges, pushes) and talk to the user. Agents do the domain work; never do an
agent's work yourself. Process and ownership rules: `docs/specs/README.md`.

Command: `$ARGUMENTS`

## new <F-NNN …> | <request>

1. `git switch dev && git pull --ff-only`. Next id = highest
   `docs/specs/SPEC-NNN-*.md` + 1. Create `spec/SPEC-NNN-<slug>` from `dev`.
2. Spawn `architect` with: the findings or request, the spec id and path, the
   base SHA (`git rev-parse --short HEAD`), and "work on the current branch of
   the main checkout".
3. Commit the spec on the spec branch (`docs(SPEC-NNN): draft spec`).
4. Show the user: requirements, contracts table, ACs, task list, open
   questions. Ask them to approve or change it. Do not continue on your own.

## approve SPEC-NNN

Only on the user's explicit instruction. Refuse if *Open questions* has
unchecked items. Set *Status* `Approved`, update the index in
`docs/specs/README.md`, add a *Changelog* line, commit.

## implement SPEC-NNN

1. Switch to the spec branch. Refuse unless *Status* is `Approved` or
   `In progress` (resume). Set `In progress`, commit.
2. Take the tasks that are `Todo` with all `Depends on` done. That is the
   current wave. Spawn one agent per task (`subagent_type` = the task's agent),
   tasks from different domains in parallel, same-domain tasks in one call.
   Prompt for each:
   - spec path, task ids, spec branch name, current spec-branch SHA;
   - "Sync your worktree to the spec branch, implement only these tasks, run
     your gate, commit, and report: branch, commit SHA, worktree path, gate
     output, deviations".
   `qa-engineer` tasks (behave tests) run in the main checkout after the
   engineer tasks they depend on are merged.
3. For each returned engineer branch:
   - `git diff --name-only <spec-branch>...<agent-branch>`: every path must be
     inside that agent's ownership (`docs/specs/README.md` § Domain agents).
     Out-of-scope paths are a deviation: don't merge, go to step 4.
   - `git merge --no-ff <agent-branch>` into the spec branch, mark the tasks
     `Done` in the spec, commit, then
     `git worktree remove <path> && git branch -d <agent-branch>`.
4. Deviation, failed gate or `Blocked`: mark the task `Blocked (<reason>)`.
   For a spec gap, spawn `architect` to amend the spec. If requirements or
   contracts changed, show the user and get re-approval before continuing.
5. Repeat from step 2 until every non-QA-verification task is `Done`. Set
   `In review`, commit, and tell the user to run `/spec verify SPEC-NNN`.

## verify SPEC-NNN

1. Switch to the spec branch. Spawn `qa-engineer` with the spec path and
   branch name.
2. Commit QA's changes to the spec and findings
   (`docs(SPEC-NNN): verification`).
3. `Done`: show the user the verification table and offer to push and open a
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
- Commits you make end with the attribution line from your session
  instructions. Agent commits carry their own `Co-Authored-By`.
- Report only what agents and commands actually returned. If an agent's
  report and the diff disagree, trust the diff and say so.
