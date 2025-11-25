# Code Review Guidelines

## General Rules

- Conduct all code reviews in English
- Focus on adherence to Python principles and PEP8 compliance
- Check for code clarity and readability
- Verify PR content is consistent with code changes
- Ensure commit names are logical and descriptive

## Code Quality Checks

### Bad Practices to Flag

- **Excessive nesting**: Maximum 3 levels of nesting
- **Type ambiguity**: Missing or incorrect type hints
- **Magic numbers**: Hardcoded values without named constants
- **Poor error handling**: Bare `except:` clauses or swallowed exceptions

### Project-Specific Patterns

#### Type Hints (Required)

- All function parameters must have type hints
- All return types must be specified
- Use modern syntax: `list[Type]`, `dict[Key, Value]`
- Example: `def process(docs: list[Document]) -> list[str]:`

#### Dependency Injection

- Use FastAPI's `Depends()` pattern
- Define dependencies in `app/core/dependencies.py`
- Use `@lru_cache()` for singleton services
- Never instantiate services directly in controllers

#### Logging

- Include context in log messages
- Appropriate levels: INFO (flow), WARNING (unexpected), ERROR (failures)
