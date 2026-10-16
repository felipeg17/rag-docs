# Contributing

Contributions are welcome. This guide covers how to set up a development environment, run tests, and submit changes.

## Development Setup

### Fork and Clone

```bash
git clone https://github.com/yourusername/rag-docs.git
cd rag-docs
git remote add upstream https://github.com/original/rag-docs.git
```

### Create a Feature Branch

```bash
git checkout -b ft-my-feature
```

Branch naming: `ft-`, `fix-`, `chore-`, `docs-` prefixes.

### Install Dependencies

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
uv pip install -e .

cd ../frontend
python -m venv .venv
source .venv/bin/activate
uv pip install -e .
```

## Development Workflow

### Run Tests and Linting

```bash
cd backend

# Run all checks
ruff check app && mypy app && pytest tests/unit -v
```

Verify:

- Tests pass (unit and integration if applicable)
- No linting errors (`ruff check`)
- No type errors (`mypy`)

### Test Integration Tests

If your changes affect APIs or workflows:

```bash
# Start backend in one terminal
uvicorn main:app --reload

# Run integration tests in another
BACKEND_URL=http://localhost:8106 behave tests/behave -v
```

## Code Style

### Python

- Follow PEP 8
- Use type hints for function signatures
- Use `ruff format` for consistent formatting
- Max line length: 88 characters

### Naming

- Functions/variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private: prefix with `_`

### Comments and Docstrings

- Avoid over-commenting; code should be self-documenting
- Use docstrings for public functions/classes (one-line preferred)
- Leave a blank line between imports and code

## Testing Requirements

### New Features

- Add unit tests in `tests/unit/`
- Add integration tests in `tests/behave/` if user-facing

### Bug Fixes

- Add a test that reproduces the bug
- Fix the bug
- Verify test passes

## Documentation

- Update relevant docs in `docs/` folder
- Keep `CLAUDE.md` in sync with major architectural changes
- Add docstrings to new functions/classes
- Update README.md if user-facing features change
