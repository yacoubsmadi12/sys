---
name: ZainJo Replit setup
description: How ZainJo LogStream is wired to run on Replit for development/preview.
---

## Setup

- **Frontend artifact**: `artifacts/zainjo-ui` (previewPath `/`) — managed workflow `artifacts/zainjo-ui: web` using pnpm workspace.
- **Backend**: Plain workflow `ZainJo Backend` running uvicorn at port 8099, config from `zainjo-logstream/config.yaml`.
- **Proxy**: `artifacts/zainjo-ui/vite.config.ts` proxies `/api` → `http://localhost:8099`. The `api-server` artifact preview path was changed to `/workspace-api` to avoid intercepting `/api` calls.
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

## Auto-discovery of sources (migration 002)

- Migration `002_auto_discovered` adds `auto_discovered` (bool), `last_seen_at` (datetime), `log_count` (int) to `log_sources`.
- `processor.py` persists unknown senders as `auto_discovered=True` rows on first packet. Module-level `_auto_discovered_ips` set + `_auto_discover_lock` prevents duplicate DB inserts across workers.
- `log_count` / `last_seen_at` batched via `_flush_counts()` every 50 messages — not per-message.
- Sources page auto-refreshes every 15 s; shows AUTO badge, Logs count, Last Seen column.

## Huawei NCE FAN hash-delimited format

- NCE FAN messages: `OperationLog%<id> # <severity> # <username> # <component> # <path>` — NOT key=value.
- First pattern in `app/parsers/huawei.py` handles this; must remain first in `_PATTERNS` list.
- Without this pattern, `username` is `None` and filter rules silently skip these messages.

**Why:** Imported project had incompatible runtime defaults, wrong DB driver options, and parsers that missed the NCE FAN `#`-delimited format.

**How to apply:** On VM, run `alembic upgrade head` after pulling, then `systemctl restart zainjo-logstream`. On Replit, run alembic manually and restart the ZainJo Backend workflow.
