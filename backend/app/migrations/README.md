# Database Migrations with Alembic

This directory contains Alembic migrations for managing the `app` schema (documents, search_interactions, qa_interactions).

## Initial Setup

Alembic is already configured. The database uses two schemas:

- `app` - Application tables (managed by Alembic migrations)
- `vector` - PGVector embeddings (managed by Langchain)

## Basic Workflow

1. Check Current Migration Status

```sh
cd backend/
alembic current
```

2. View Migration History

```sh
alembic history --verbose
```

3. Run Migrations (Upgrade to Latest)

```sh
alembic upgrade head
```

4. Rollback Migration

```sh
# Rollback one version
alembic downgrade -1

# Rollback to specific version
alembic downgrade <revision_id>
```

## Creating New Migrations

### Auto-generate from Model Changes

1. Edit ORM models in `backend/app/infrastructure/database/models.py`

2. Generate migration:

   ```sh
   alembic revision --autogenerate -m "Add column to documents"
   ```

3. Review the generated file in `app/migrations/versions/`

4. Run migration:
   ```sh
   alembic upgrade head
   ```

### Manual Migration (Empty Template)

```sh
# Create empty migration file
alembic revision -m "Custom migration"

# Edit the generated file and add upgrade/downgrade logic
```

## Common Commands

```sh
alembic current                    # Show current version
alembic history                    # List all migrations
alembic upgrade head               # Apply all pending migrations
alembic upgrade +1                 # Apply next migration
alembic downgrade -1               # Rollback last migration
alembic upgrade <revision>         # Upgrade to specific version
alembic downgrade <revision>       # Downgrade to specific version
alembic upgrade head --sql         # Show SQL without executing
alembic stamp head                 # Mark DB as migrated without running
```

## Notes

- Schemas (`app`, `vector`) are created by PostgreSQL init scripts, not migrations
- Always review auto-generated migrations before applying
- Don't edit old migrations - create new ones to fix issues
