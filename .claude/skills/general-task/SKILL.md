---
name: general-task
description: >
  Structured task runner with lean operating rules. Use this skill whenever the user
  invokes /task to execute any software engineering task. Enforces: no assumptions,
  codebase exploration before acting, model selection by complexity (haiku → sonnet → opus),
  minimal verbosity, explicit clarification on blockers, and dead-end escalation.
---

## Input

```
task: <description>
context: <optional background>
adds: <additional rules>
```

Parse the first line as the task. If a `context:` line follows, treat it as additional grounding.

## Model selection

Pick the model based on task complexity to minimize token cost:

| Complexity | Model | Examples |
|------------|-------|---------|
| Simple | **haiku** | Read files, run commands, grep, list dirs, fetch a single value |
| Medium | **sonnet** | Multi-step edits, test runs, debugging with a known surface area |
| Complex | **opus** | Architecture decisions, broad refactors, ambiguous or cross-cutting problems |

When spawning subagents for isolated subtasks (e.g., file reads, shell commands), use haiku.

## Operating rules

- **Ground everything**: base decisions on what you observe — code, file contents, command output. No guessing.
- **Explore before acting**: if the task touches unfamiliar code, search and read first.
- **No verbosity**: skip greetings, restating the task, and trailing summaries. One sentence per update is enough.
- **Ask on true blockers**: if a required piece of information can't be derived, ask one focused question — not multiple at once.
- **Surface dead-ends explicitly**: if a path is blocked or leads nowhere, say so and ask for new guidance rather than spinning.
- **Files edition**: scope changes to the entire files, not just line by line.

## Execution flow

1. Read the task and context.
2. Identify knowns vs. what needs verification in the codebase.
3. Explore/verify with the right model
4. Create solution alternatives with pros and cons.
5. Ask the user for the approach to implement.
6. Ellaborate a plan with the defined approach.
7. Execute the proposed plan.
9. Audit the results against the plan.
10. Report the outcome in one or two sentences.
