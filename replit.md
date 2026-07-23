# ZainJo LogStream

Production-ready on-premise Syslog Collector and Log Management Platform for Telecom NOC environments.

## What is this?

This Replit workspace contains the **complete source code** for ZainJo LogStream.
The application is designed to be deployed on an Ubuntu Linux VM in a telecom environment,
but it can also be run here on Replit for development/preview.

## Source code location

All application code is under `zainjo-logstream/`:

```
zainjo-logstream/
├── backend/           # Python 3.12 + FastAPI backend
│   ├── app/
│   │   ├── main.py          # FastAPI app + lifecycle
│   │   ├── config.py        # pydantic-settings from config.yaml
│   │   ├── database.py      # Async SQLAlchemy + session factory
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   ├── api/routes/      # REST API endpoints
│   │   ├── syslog/          # UDP/TCP listeners + RFC 3164/5424 parser
│   │   ├── parsers/         # Vendor parsers (Huawei, Nokia, Ericsson)
│   │   ├── workers/         # Processor, SIEM forwarder, cleanup
│   │   └── auth/            # JWT + bcrypt
│   ├── alembic/             # Database migrations
│   └── requirements.txt
├── frontend/          # React 18 + Vite + TypeScript + Tailwind CSS
│   └── src/
│       ├── pages/           # Dashboard, Sources, Filters, LogSearch, Audit
│       ├── components/      # Layout, etc.
│       ├── api/             # Axios client + TypeScript types
│       └── hooks/           # useAuth
├── deployment/
│   ├── syslog-collector.service  # systemd unit file
│   └── nginx.conf                # Nginx reverse proxy config
├── config.yaml.example   # Configuration template
├── config.yaml           # Active Replit config (auto-generated)
├── schema.sql            # Plain SQL schema (alternative to Alembic)
├── install.sh            # One-command installer for Ubuntu
└── README.md             # Full documentation
```

## Running on Replit (Development)

Two workflows are configured:

| Workflow | Command | Port |
|----------|---------|------|
| **ZainJo Frontend** | `cd zainjo-logstream/frontend && npm run dev` | $PORT (default 3000) |
| **ZainJo Backend**  | `cd zainjo-logstream/backend && uvicorn app.main:app --host 0.0.0.0 --port 8080` | 8080 |

### Default credentials
- **Username:** `admin`
- **Password:** `Admin@LogStream1`

### Backend config
Edit `zainjo-logstream/config.yaml` to change settings.
Database migrations: `cd zainjo-logstream/backend && CONFIG_PATH=../config.yaml alembic upgrade head`

### bcrypt note
Replit uses Python 3.13 which requires `bcrypt==4.0.1` (pinned via uv). Do not upgrade bcrypt.

## Deployment target (Production)

- **OS**: Ubuntu 22.04 / 24.04 LTS
- **VM**: 32 vCPU, 62 GB RAM, 900 GB `/data` disk
- **Syslog port**: 1514 UDP+TCP
- **Web UI**: port 80 via Nginx
- **API**: port 8080 (proxied by Nginx)
- **SIEM integration**: forwards accepted logs to `http://localhost:5000/api/logs`
- Run `sudo bash install.sh` on the target VM

## Key features

- Async UDP/TCP syslog listener (asyncio, handles millions of logs/day)
- 100,000-entry in-memory ingestion queue, 8 parallel processor workers
- Source management (Huawei NCE/U2020, Nokia NetAct, Ericsson ENM)
- Username/regex filter engine — dropped logs never reach SIEM
- SIEM forwarding with 3-attempt retry + dead-letter file backup
- Daily flat-file storage with gzip compression + 90-day retention cleanup
- Vendor parsers (username, operation, device, result extraction)
- JWT authentication with Admin/Viewer roles
- React dashboard: Overview, Sources, Filter Rules, Log Search, Audit

## Stack

- Python 3.12, FastAPI, SQLAlchemy 2.0 (async), asyncpg, Alembic
- PostgreSQL (primary datastore — Replit managed DB in dev)
- React 18, Vite, TypeScript, Tailwind CSS, Recharts, TanStack Query
- Nginx, systemd (production only)

## User preferences

- Target: Ubuntu Linux VM in telecom environment
- Existing SIEM on port 5000 must not be disturbed
- bcrypt must stay at 4.0.1 for Python 3.13 compatibility
