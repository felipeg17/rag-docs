# Code Review Guidelines

## Review Priorities

Focus on these in order:

1. **Correctness** - Does the code work?
2. **Design** - Is the solution well-architected? Are there better approaches?
3. **Maintainability** - Is the code readable and easy to modify?
4. **Testing** - Are tests meaningful and cover critical paths?
5. **Performance** - Will this scale? Are there inefficiencies?
6. **Style** - Does it follow conventions? (lowest priority)

## Review Process

1. Read PR description to understand the goal
2. Review tests first to understand expected behavior
3. Review main logic for correctness and design
4. Check error handling and edge cases
5. Suggest improvements, not just flag issues
6. Provide specific fixes when possible

---

## Logic & Functionality

### Questions to Ask

- Does this solve the right problem?
- Are there edge cases not handled (empty inputs, null values, boundary conditions)?
- Are assumptions documented and validated?
- Is the algorithm correct (loops, conditionals, early returns)?
- Are there potential race conditions in async/concurrent code?

### Common Bugs to Flag

- Off-by-one errors in loops and array slicing
- Null/None dereferencing without checks
- Incorrect boolean logic (and vs or, negation errors)
- Resource leaks (unclosed files, connections, sessions)
- Infinite loops or incorrect termination conditions
- Mutable default arguments causing shared state bugs
- Modifying collections while iterating over them
- Type mismatches between function parameters and arguments

---

## Design & Architecture

### Design Questions

- Is this the right abstraction (not too generic or too specific)?
- Does it follow existing patterns in the codebase?
- Is there unnecessary complexity that could be simplified?
- Are responsibilities clear (Single Responsibility Principle)?
- Is it extensible for future changes?

### Code Smells

- God objects/functions doing too much (>50 lines, multiple responsibilities)
- Feature envy (methods using another class's data extensively)
- Primitive obsession (many primitive parameters instead of objects)
- Duplicate code across multiple locations
- Long parameter lists (>4 parameters)
- Shotgun surgery (one change touches many unrelated files)

### Suggest Solutions

- Extract duplicated logic to shared helpers
- Split functions with multiple responsibilities
- Group related parameters into configuration objects
- Propose specific refactoring approaches

---

## Error Handling & Edge Cases

### What to Check

- What can fail (network, I/O, external APIs, database)?
- Are errors handled gracefully with proper exceptions?
- Is cleanup guaranteed (use context managers)?
- Are error messages helpful with context for debugging?
- Is error handling too broad (avoid bare except)?

### Edge Cases

- Empty collections (lists, dicts, strings)
- None/null values
- Zero and negative numbers (division by zero)
- Very large inputs (memory/performance issues)
- Invalid user input (malformed data, wrong types)
- Concurrent access (race conditions)
- Timeout scenarios for external calls
- Boundary values (min/max, empty, single-element)

---

## Testing Quality

### Coverage Questions

- Are critical paths tested (happy path AND error cases)?
- Are edge cases tested (boundary values, empty, None)?
- Are tests independent (no shared state)?
- Are assertions meaningful (testing behavior, not implementation)?
- Is test data realistic?

### Quality Issues

- Fragile tests that break on minor refactoring
- Unclear test names (use descriptive names explaining what is tested)
- Missing assertions or only asserting True
- Over-mocking (mocking everything, testing nothing real)
- No negative tests (only success cases)
- Testing multiple behaviors in one test

---

## Security

### Common Vulnerabilities

- **Injection attacks**: SQL, command, prompt injection
  - Use parameterized queries, avoid string concatenation
- **Hardcoded secrets**: API keys, passwords in code
  - Use environment variables or secret managers
- **Unsafe deserialization**: pickle, eval(), exec() on untrusted data
  - Use JSON/YAML, validate before deserializing
- **Path traversal**: User-controlled file paths
  - Validate paths, use allowlists
- **Unvalidated redirects**: Redirecting to arbitrary URLs
  - Validate against safe URL allowlist

### Input Validation

- All user input must be validated (type, length, format)
- Sanitize before using in queries, commands, or templates
- Never trust external data (files, APIs, user input)

---

## Performance

### Anti-Patterns

- N+1 queries (loop making individual DB/API calls - batch instead)
- Inefficient algorithms (O(n²) when O(n) or O(n log n) exists)
- Unnecessary repeated computations (calculate once, cache)
- Large data in memory (stream or paginate instead)
- Blocking I/O in loops (use async for parallel operations)
- Missing database indices on queried columns
- String concatenation in loops (use join instead)

### Questions

- Will this scale with 10x, 100x data?
- Are there repeated expensive operations?
- Can results be cached?
- Are we loading more data than needed?

---

## Code Readability

### Clarity Standards

- Functions < 50 lines (extract smaller functions if longer)
- Cyclomatic complexity < 10 (too many branches/conditions)
- Descriptive names (no abbreviations like `dc`, `ul`)
- Function names as verb phrases (`calculate_total`, not `data`)
- Boolean names as questions (`is_valid`, not `check`)
- Comments explain "why" not "what"
- Maximum 3 levels of nesting (use early returns)

### Refactoring

- Replace magic numbers with named constants
- Extract nested conditionals to guard clauses
- Replace comments with better variable/function names
- Split long functions into focused smaller ones

---

## Python Best Practices

### Modern Patterns (Python 3.10+)

- Type hints everywhere with modern syntax: `list[str]`, `dict[str, int]`, `str | None`
- Prefer comprehensions over loops when readable
- Use context managers for resources (`with` statements)
- Use `pathlib.Path` instead of `os.path`
- Prefer f-strings over `.format()` or concatenation
- Use `Enum` for constants, `dataclass` for data containers

### Anti-Patterns

- Mutable default arguments (`def func(items=[])`)
- Using `==` for None (use `is None`)
- Catching `Exception` broadly without re-raising
- Using `import *`
- Modifying list while iterating
- Not using generators for large datasets

---

## Code Style

### General

- Review in English
- Focus on substance over style (logic > formatting)
- Verify PR content matches code changes
- Ensure descriptive commit messages
- No redundant TODO comments if tracked as issues

### Python Style (PEP8)

- Line length: 88-100 characters
- Indentation: 4 spaces (never tabs)
- Naming: `snake_case` functions/variables, `PascalCase` classes, `UPPER_CASE` constants
- Imports: grouped (stdlib, third-party, local) and alphabetized
- Docstrings for public functions/classes

### Before Manual Review

Ensure automated tools pass: linters (ruff), formatters (ruff), type checkers (mypy), tests (pytest)
