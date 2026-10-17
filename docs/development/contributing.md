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

cd ../frontend   # requires Node 24 and npm
npm ci
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

Frontend:

```bash
cd frontend
npm run check:api && npm run lint && npm run typecheck && npm test && npm run build
```

### API Types

The frontend's request and response types are generated from the backend's OpenAPI schema and never
hand-written. After changing a backend request/response model or route:

```bash
cd backend
uv run python export_openapi.py        # rewrites backend/openapi.json
cd ../frontend
npm run gen:api                         # rewrites src/api/openapi_gen.ts
npm run typecheck                       # fix any UI code the schema change broke
```

Commit `backend/openapi.json` and `frontend/src/api/openapi_gen.ts` together. Never edit either by hand.
The backend unit test `openapi_snapshot_test.py` and `npm run check:api` (in CI) fail when they drift.
Generation is not part of `build`, `test` or the Docker image.

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

### TypeScript (frontend)

- Follow the [Google TypeScript Style Guide](https://google.github.io/styleguide/tsguide.html), enforced
  through `frontend/biome.jsonc`
- Biome is the only linter and formatter: run `npm run lint` (check) or `npm run format` (fix)
- Generated `src/api/openapi_gen.ts` is excluded from Biome

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

- Backend: add unit tests in `tests/unit/`
- Frontend: add a `*.test.ts(x)` next to the code (vitest)
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
