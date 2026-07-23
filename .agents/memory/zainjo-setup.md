---
name: ZainJo Replit setup
description: How ZainJo LogStream is wired to run on Replit for development/preview.
---

## Setup

- **Frontend artifact**: `artifacts/zainjo-ui` (previewPath `/`) — managed workflow `artifacts/zainjo-ui: web` using pnpm workspace.
- **Backend**: Plain workflow `ZainJo Backend` running uvicorn at port 8099, config from `zainjo-logstream/config.yaml`.
- **Proxy**: `artifacts/zainjo-ui/vite.config.ts` proxies `/api` → `http://localhost:8099`.
- **Database**: Replit managed PostgreSQL (`heliumdb`). Migrations run via `cd zainjo-logstream/backend && CONFIG_PATH=../config.yaml alembic upgrade head`.

## Python runtime

- **Use system Python 3.12** (not uv — uv requires ≥3.13 which is unavailable). Backend workflow command: `python -m uvicorn ...` (not `uv run uvicorn ...`).
- Packages installed via `pip install` into the Replit system Python environment (`/home/runner/workspace/.pythonlibs`).
- **`bcrypt==4.0.1`** pinned — passlib + Python 3.12 breaks with bcrypt ≥ 5.x.
- **`PyJWT`** required — `app/auth/security.py` uses `import jwt` (PyJWT package, not python-jose).
- **`python-jose`** is NOT the JWT library used by this codebase despite being in requirements.txt. The code uses `import jwt` (PyJWT).

## Frontend

- pnpm workspace dependencies must be installed (`pnpm install` at workspace root) before `artifacts/zainjo-ui: web` workflow can start.
- `zainjo-logstream/frontend` has a separate standalone npm setup (used by `ZainJo Frontend` workflow). Both frontends are similar; the artifact version (`artifacts/zainjo-ui`) is the primary one.

## config.yaml

- Lives at `zainjo-logstream/config.yaml` (not committed; derived from `config.yaml.example`).
- Key Replit overrides: `database_url` must use `postgresql+asyncpg://postgres:password@helium/heliumdb`, `log_file: ""` (no file logging), `storage_path: /tmp/zainjo-syslog`, `siem_enabled: false`, `api_port: 8099`.

## Default admin

- First-run auto-creates a default admin user (hardcoded in `_ensure_default_admin` in `app/main.py`). The credential must be changed immediately after first login — see task #3.

**Why:** The imported project was generated with incompatible runtime defaults and libpq-style database options; without these translations the workflows either could not install, could not import, or exited during startup.

**How to apply:** When restoring this project or changing its workflows, keep system Python 3.12, install bcrypt==4.0.1 and PyJWT explicitly, and run alembic migrations before first start.
