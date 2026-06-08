# Code Review Guidelines

## Priorities

1. **Correctness** — logic, edge cases, algorithm accuracy
2. **Design** — right abstraction, follows existing patterns, SRP
3. **Maintainability** — readability, complexity, naming
4. **Testing** — critical paths covered, meaningful assertions
5. **Performance** — scaling, N+1s, unnecessary computation
6. **Style** — PEP8, conventions

## Process

1. Read PR description first
2. Review tests to understand expected behavior
3. Review logic for correctness and design
4. Suggest improvements, not just flag issues — provide specific fixes when possible

---

## Logic

Flag these specifically:

- Off-by-one errors in loops/slicing
- Mutable default arguments (`def f(items=[])`)
- Modifying collections while iterating
- Resource leaks (unclosed files, connections, sessions)
- Incorrect boolean logic (and/or confusion, negation errors)

---

## Design

Code smells to flag:

- Functions > 50 lines or with multiple responsibilities
- Duplicate logic across locations — suggest shared helpers
- Long parameter lists (> 4) — suggest grouping into objects
- Feature envy (method relies heavily on another class's data)

---

## Error Handling

- Avoid bare `except` — catch specific exceptions
- Guarantee cleanup with context managers
- Error messages must include context for debugging
- Don't ignore failures from network, I/O, or external APIs

---

## Testing

Flag:

- Missing negative/error-case tests
- Tests that assert `True` only or test implementation instead of behavior
- Over-mocking (tests nothing real)
- Shared state between tests

---

## Security

- No hardcoded secrets — use env vars or secret managers
- Parameterized queries only — no string concatenation in SQL
- Validate all user input at system boundaries (type, length, format)
- Never use `eval()`/`exec()`/`pickle` on untrusted data

---

## Performance

Flag:

- N+1 queries inside loops — batch instead
- Repeated expensive computations — calculate once or cache
- O(n²) where O(n log n) exists
- Loading full datasets into memory when streaming/pagination fits

---

## Python (3.10+)

Enforce:

- Type hints with modern syntax: `list[str]`, `str | None`
- `is None` / `is not None` — never `== None`
- `pathlib.Path` over `os.path`
- f-strings over `.format()` or concatenation
- `Enum` for constants, `dataclass` for data containers

---

## Style

- Review in English
- Descriptive names: no abbreviations (`dc`, `ul`); booleans as questions (`is_valid`)
- Comments explain *why*, not *what*
- Max 3 levels of nesting — use early returns
- Verify PR description matches the actual changes
