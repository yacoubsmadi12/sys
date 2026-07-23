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

- `bcrypt==4.0.1` is pinned because passlib + Python 3.13 breaks with bcrypt ≥ 5.x (ValueError: password cannot be longer than 72 bytes).
- Default admin credentials: username `admin`, password `Admin@LogStream1`.

## How to apply

- If bcrypt is ever upgraded, downgrade it back to 4.0.1 via `uv add bcrypt==4.0.1`.
- After any schema change in the Python backend, re-run the alembic migration command above.
- Do NOT use `@apply <custom-component-class>` inside another `@layer components` block in Tailwind v4 — expand the styles directly.
