# Development

Instructions for contributing to the **FastFrame framework** repository.

## Setup

1. Clone the repository.
2. Create a virtual environment (Python 3.11+).
3. Install in editable mode with dev dependencies:

   ```text
   pip install -e ".[dev]"
   ```

4. Run tests:

   ```text
   pytest
   ```

5. Lint:

   ```text
   ruff check src tests
   ```

## Fixture project

Integration tests use `tests/fixtures/miniproject/`. To run the dev server manually:

```text
cd tests/fixtures/miniproject
python manage.py runserver
```

Then open `http://127.0.0.1:8000/health`.

Apply migrations (required before using models):

```text
python manage.py migrate
python manage.py makemigrations -n describe_change
```

Create a new project from the framework repo:

```text
fastframe startproject mysite
cd mysite
pip install -e /path/to/fast-frame   # install fastframe
python manage.py migrate
python manage.py runserver
python manage.py test
```

## Documentation changes

- Product docs live in `docs/`.
- Architectural decisions: add an ADR under `adr/` for significant choices.
- Keep [public-api-v0.1.md](public-api-v0.1.md) in sync when stabilizing APIs.

## Release process (future)

Not defined for 0.0.0 scaffolding. Pre-1.0 releases will follow SemVer with changelog entries in [CHANGELOG.md](../CHANGELOG.md).
