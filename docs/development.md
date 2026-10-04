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
   scripts/pylint-check.sh
   ```

   Pylint warnings (exit 4 or 6) are allowed. The script fails on exit 2, or on an E/F message.

6. Install the pre-commit hook. It formats staged Python with Ruff, applies Ruff lint fixes, and runs the same Pylint check when a framework source file is staged:

   ```text
   pre-commit install
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
- Architectural decisions: add an ADR under `docs/adr/` for significant choices. If the implementation moves without rejecting the decision, append an Addition and leave the original text in place.
- Keep [public-api-v0.1.md](public-api-v0.1.md) in sync when stabilizing APIs.

## Release process

Releases are tagged and published to PyPI as the distribution `fast-frame`. The current package release is **0.1.3**. Pre-1.0 releases follow SemVer with changelog entries in [CHANGELOG.md](https://github.com/0xdps/fast-frame/blob/trunk/CHANGELOG.md). `fastframe.__version__` is still `0.1.0`; the version commands print that string.
