---
name: ZainJo Replit setup
description: How ZainJo LogStream is wired to run on Replit for development/preview.
---

## Setup

- **Frontend artifact**: `artifacts/zainjo-ui` (previewPath `/`) — ZainJo frontend source files copied from `zainjo-logstream/frontend/src/` into `artifacts/zainjo-ui/src/`. Uses Tailwind v4; `@apply badge` chaining not allowed — expand badge classes inline instead.
- **Backend**: Plain workflow `ZainJo Backend` running uvicorn at port 8080, config from `zainjo-logstream/config.yaml`.
- **Proxy**: `artifacts/zainjo-ui/vite.config.ts` proxies `/api` → `http://localhost:8080`.
- **Database**: Replit managed PostgreSQL (`heliumdb`). Migrations run via `cd zainjo-logstream/backend && CONFIG_PATH=../config.yaml alembic upgrade head`.

## Why

- `bcrypt==4.0.1` is pinned because passlib + Python 3.13 breaks with bcrypt ≥ 5.x due to bcrypt's input-length behavior.

## How to apply

- If bcrypt is ever upgraded, downgrade it back to 4.0.1 via `uv add bcrypt==4.0.1`.
- After any schema change in the Python backend, re-run the alembic migration command above.
- Do NOT use `@apply <custom-component-class>` inside another `@layer components` block in Tailwind v4 — expand the styles directly.

## Replit runtime compatibility

- The workspace must use Python 3.13 because `pyproject.toml` and `uv.lock` require `>=3.13`; use the Replit `python-base-3.13` module.
- Replit's `DATABASE_URL` may be a `postgresql://` URL with `sslmode`; the async SQLAlchemy boundary must convert the driver to `postgresql+asyncpg` and translate SSL mode to asyncpg's `ssl` connection argument.
- The managed artifact API uses port 8080, so the imported Python backend uses port 8099 to avoid a collision. Replit preview paths should point at the intended service.

**Why:** The imported project was generated with incompatible runtime defaults and libpq-style database options; without these translations the workflows either could not install, could not import, or exited during startup.

**How to apply:** When restoring this imported project or changing its workflows, keep the locked Python runtime and async database URL normalization aligned with the managed artifact services.
