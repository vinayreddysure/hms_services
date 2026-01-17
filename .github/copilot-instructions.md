# Copilot / AI agent instructions for this repository

This repo is a small FastAPI backend using SQLModel/SQLite. Use these notes to be immediately productive when editing, adding endpoints, or running local tests.

Key files and responsibilities
- `main.py` — FastAPI app and router registration. New route modules should expose an `APIRouter` and be imported/registered here (or follow the existing pattern in `main.py`).
- `app/routes/users.py` — example router. Routes use `app.crud` for data operations and `app.schemas` for request/response shapes.
- `app/crud.py` — data access helpers that call `sqlmodel.Session`. NOTE: currently `crud.py` uses `Session()` directly while `app/database.py` defines `engine` and `get_session()`; expect an inconsistency and prefer creating sessions with `Session(engine)` or using the `get_session` generator pattern.
- `app/models.py` — persistent models (SQLModel, table=True). Fields use `Field(...)` and types are standard Python types.
- `app/schemas.py` — pydantic-style request/response schemas. Use these types for route signatures (e.g., `schemas.UserCreate`).
- `app/database.py` — engine creation and DB session helper. Configured currently to `sqlite:///./test.db` and `create_engine(..., echo=True)` (SQL logs enabled).
- `requirements.txt` — runtime and dev deps: `fastapi`, `uvicorn`, `sqlmodel`, `pytest`, `alembic`, etc.

Run & debug
- Start the dev server: `uvicorn main:app --reload` from repo root. This is the primary way to iterate on endpoints.
- DB file: default is `./test.db` (SQLite). SQL logging is on due to `echo=True` in `app/database.py`.
- Tests: `pytest` (repo currently has pytest listed; if you add tests, use `pytest-asyncio` for async test cases).

Code patterns / conventions to follow
- Routes: create a module under `app/routes/` with an `APIRouter()` named `router`. In `main.py`, routers are included with `app.include_router(users.router, prefix="/users", tags=["Users"])` — follow this pattern for new resources.
- CRUD vs Schemas: keep data access logic in `app/crud.py` (simple helpers) and use `app/schemas.py` for request shapes. Models in `app/models.py` are the SQLModel ORM definitions.
- DB sessions: prefer explicit sessions created with the `engine` in `app/database.py` (e.g., `with Session(engine) as session:`) or implement a dependency `get_session()` and inject it into routes. See `app/database.py` for the engine config.
- Empty modules: `app/__init__.py`, `app/utils.py`, and `app/routes/__init__.py` are present but empty; they are safe places to add package-level helpers or to centralize route imports.

Discovered inconsistencies / gotchas (to watch or fix)
- `crud.py` calls `Session()` without an engine argument which will fail at runtime unless a default Session was configured. Prefer `Session(engine)` or refactor crud to accept a session argument or dependency injection.
- Alembic is listed in `requirements.txt` but there are no migrations in the repo. If you add migrations, keep `alembic` config in sync with `app/database.py`'s `DATABASE_URL`.

Quick examples
- Add a new route module:
  - create `app/routes/items.py` with `router = APIRouter()` and endpoints
  - import and include the router in `main.py` (or centralize in `app/routes/__init__.py` and import that)

- Start server locally:
```
uvicorn main:app --reload
```

When editing: prioritize small, testable changes. For DB work prefer adding unit tests that exercise `crud` functions and route handlers. If you make DB-session changes, update all `crud` usages.

If anything here is unclear or you want more details (tests, CI commands, or how to wire Alembic), tell me which section to expand and I will update this file.
