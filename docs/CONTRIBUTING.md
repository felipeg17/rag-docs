# Contributing

Contributions are welcome. This guide covers how to set up a development environment, run tests, and submit changes.

## Development Setup

### 1. Fork and Clone

```bash
git clone https://github.com/yourusername/rag-docs.git
cd rag-docs
git remote add upstream https://github.com/original/rag-docs.git
```

### 2. Create a Feature Branch

```bash
git checkout -b feature/my-feature
```

Branch naming: `feature/`, `bugfix/`, `chore/`, `docs/` prefixes.

### 3. Install Dependencies

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

See [SETUP.md](SETUP.md) for detailed environment setup.

## Development Workflow

### 1. Make Changes

Edit code, write tests, ensure backwards compatibility.

### 2. Run Tests and Linting

```bash
cd backend

# Run all checks
ruff check app && mypy app && pytest tests/unit -v
```

Verify:
- Tests pass (unit and integration if applicable)
- No linting errors (`ruff check`)
- No type errors (`mypy`)

### 3. Format Code

```bash
ruff format app
```

### 4. Test Integration Tests (Optional)

If your changes affect APIs or workflows:

```bash
# Start backend in one terminal
uvicorn main:app --reload

# Run integration tests in another
BACKEND_URL=http://localhost:8106 behave tests/behave -v
```

### 5. Commit Changes

Write clear, descriptive commits:

```bash
git add .
git commit -m "Add feature: reranking support for semantic search"
```

Commit message format:
- Start with verb: "Add", "Fix", "Refactor", "Improve", "Docs"
- Be specific about what changed
- Reference issues if applicable: "Fixes #123"

### 6. Push and Open PR

```bash
git push origin feature/my-feature
```

Create a pull request on GitHub with:
- Clear title
- Description of changes
- Steps to test (if UI changes)
- Links to related issues

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

### Imports

Organize in groups with blank lines:

```python
import os
import sys

import numpy as np
from fastapi import FastAPI

from app.services import QAService
from app.core.config import settings
```

### Comments and Docstrings

- Avoid over-commenting; code should be self-documenting
- Use docstrings for public functions/classes (one-line preferred)
- Leave a blank line between imports and code

```python
def retrieve_and_rank(query: str, top_k: int = 5) -> list[str]:
    """Retrieve chunks and rerank by relevance."""
    chunks = self.vector_db.retrieve(query)
    return self.reranker.rank(chunks, query)[:top_k]
```

## Testing Requirements

### New Features

- Add unit tests in `tests/unit/`
- Add integration tests in `tests/behave/` if user-facing

### Bug Fixes

- Add a test that reproduces the bug
- Fix the bug
- Verify test passes

### Coverage

Run `pytest --cov=app` and aim for >80% coverage on changed code.

## Database Changes

If modifying models in `app/models/`:

1. Create a migration:
   ```bash
   cd backend
   alembic revision --autogenerate -m "Add new field"
   ```

2. Review the generated migration in `app/migrations/versions/`

3. Test migrations:
   ```bash
   alembic upgrade head
   alembic downgrade -1
   alembic upgrade head
   ```

4. Commit the migration file

## Documentation

- Update relevant docs in `docs/` folder
- Keep `CLAUDE.md` in sync with major architectural changes
- Add docstrings to new functions/classes
- Update README.md if user-facing features change

## PR Review Process

- Address requested changes in new commits (don't force-push)
- Respond to comments or ask for clarification
- Ensure CI passes (GitHub Actions)
- Request re-review after making changes

## Releasing

Releases are managed by maintainers. If proposing a release:

1. Update version in `backend/pyproject.toml` and `frontend/pyproject.toml`
2. Update `CHANGELOG.md` (if it exists)
3. Create a GitHub release with release notes

## Getting Help

- Check existing issues and discussions
- Ask in pull request comments
- Open an issue with a clear description and steps to reproduce (for bugs)

## Code of Conduct

Be respectful and constructive in all interactions.

---

Thank you for contributing to rag-docs!
