# task-manager

A small Flask + SQLAlchemy JSON API for to-do tasks. Used for the Week 9 drills.

## Commands

- Install: `pip install -r requirements.txt`
- Run the app: `python run.py`
- Tests: `pytest -q`
- Coverage: `pytest --cov=app --cov-report=term-missing`
- Lint: `ruff check .`
- Format: `ruff format .`

## Architecture

- `app/routes/` holds thin HTTP handlers. They parse the request, call a service, and return JSON.
- `app/services/` holds all business logic and all database access.
- `app/models.py` holds the SQLAlchemy models and the allowed values (`TaskStatus`, `PRIORITIES`).
- `app/errors.py` defines `AppError`, `ValidationError` and `NotFoundError`. Services raise these;
  a single error handler turns them into JSON responses.
- Tests use an in-memory SQLite database from the `app` fixture in `tests/conftest.py`.

## Conventions

- Raise `ValidationError` or `NotFoundError` from services. Never raise bare `ValueError` or `Exception`.
- Use the `TaskStatus` constants, not string literals, for task status.
- Every new service function gets tests in `tests/` in the same commit.
- Docstrings on every public function.

## Do not touch

- When asked to implement code so that tests pass, do not modify any file in `tests/`.
- Do not edit `tests/conftest.py` unless asked.
