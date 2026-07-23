# ZainJo LogStream

**Production-ready Syslog Collector and Log Management Platform for Telecom NOC environments.**

Collects, filters, stores, searches, and forwards syslog messages from Huawei, Nokia, and Ericsson network management systems.

---

## Architecture

```
┌─────────────────────┐   UDP/TCP    ┌──────────────────────────────────┐
│  Huawei NCE / U2020  │────────────▶│                                  │
│  Nokia NetAct        │   :1514     │       ZainJo LogStream           │
│  Ericsson ENM        │────────────▶│                                  │
└─────────────────────┘             │  ┌────────────┐  ┌────────────┐  │
                                    │  │   Syslog   │  │  Filter    │  │
                                    │  │  Listener  │  │  Engine    │  │
                                    │  └─────┬──────┘  └─────┬──────┘  │
                                    │        │                │         │
                                    │  ┌─────▼────────────────▼──────┐  │
                                    │  │     Async Queue (100k)      │  │
                                    │  └─────────────┬──────────────┘  │
                                    │                │                  │
                                    │  ┌─────────────▼──────────────┐  │
                                    │  │  8× Processor Workers       │  │
                                    │  │  (parse, filter, store)     │  │
                                    │  └──┬──────────────────────┬───┘  │
                                    │     │                      │       │
                                    │  ┌──▼──────┐  ┌───────────▼────┐  │
                                    │  │  Postgres│  │  /data/syslog  │  │
                                    │  │   DB     │  │  (flat files)  │  │
                                    │  └──────────┘  └────────────────┘  │
                                    │         │                          │
                                    │  ┌──────▼─────────┐               │
                                    │  │ SIEM Forwarder  │──▶ :5000     │
                                    │  │ (with retry)    │               │
                                    │  └─────────────────┘               │
                                    └──────────────────────────────────┘
                                                  │
                                             ┌────▼────┐
                                             │  Nginx  │
                                             │   :80   │
                                             └────┬────┘
                                                  │
                                    ┌─────────────▼──────────────┐
                                    │     React Dashboard        │
                                    │  Overview │ Sources        │
                                    │  Filters  │ Log Search     │
                                    │  Audit                     │
                                    └────────────────────────────┘
```

---

## Server Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU      | 8 vCPU  | 32 vCPU (your spec) |
| RAM      | 16 GB   | 62 GB (your spec) |
| OS Disk  | 50 GB   | 200 GB |
| Log Disk | 200 GB  | 900 GB at `/data` |
| OS       | Ubuntu 22.04 LTS | Ubuntu 22.04+ |

---

## Quick Installation

```bash
# 1. Clone/copy the project to the server
scp -r zainjo-logstream/ user@your-vm:/tmp/

# 2. Run the installer as root
cd /tmp/zainjo-logstream
sudo bash install.sh
```

The installer:
- Installs Python 3.12, Node.js 20, PostgreSQL, Nginx
- Creates the `logstream` system user
- Sets up the PostgreSQL database with a random password
- Builds and deploys the React frontend
- Runs database migrations
- Installs and starts the systemd service
- Configures Nginx as reverse proxy
- Opens firewall ports (1514/UDP+TCP, 80/TCP)

---

## Manual Installation

If you prefer to install step by step:

```bash
# ── System packages ─────────────────────────────────────────
sudo apt-get install -y python3.12 python3.12-venv python3-pip \
    build-essential libpq-dev postgresql nginx

# Node.js 20
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo bash -
sudo apt-get install -y nodejs

# ── Database ────────────────────────────────────────────────
sudo -u postgres psql -c "CREATE USER logstream WITH PASSWORD 'YOURPASS';"
sudo -u postgres psql -c "CREATE DATABASE logstream OWNER logstream;"

# ── Application directories ─────────────────────────────────
sudo mkdir -p /opt/zainjo-logstream /etc/zainjo-logstream /var/log/zainjo-logstream
sudo mkdir -p /data/syslog/{raw/{huawei,nokia,ericsson},archive,processed,failed}
sudo useradd --system --shell /usr/sbin/nologin logstream

# ── Backend ─────────────────────────────────────────────────
sudo cp -r backend/ /opt/zainjo-logstream/backend/
python3.12 -m venv /opt/zainjo-logstream/venv
/opt/zainjo-logstream/venv/bin/pip install -r backend/requirements.txt

# ── Configuration ────────────────────────────────────────────
sudo cp config.yaml.example /etc/zainjo-logstream/config.yaml
sudo nano /etc/zainjo-logstream/config.yaml   # Set database_url, secret_key

# ── Database migrations ──────────────────────────────────────
cd /opt/zainjo-logstream/backend
CONFIG_PATH=/etc/zainjo-logstream/config.yaml \
    /opt/zainjo-logstream/venv/bin/alembic upgrade head

# ── Frontend ─────────────────────────────────────────────────
sudo cp -r frontend/ /opt/zainjo-logstream/frontend/
cd /opt/zainjo-logstream/frontend
sudo npm install && sudo npm run build

# ── Nginx ────────────────────────────────────────────────────
sudo cp deployment/nginx.conf /etc/nginx/sites-available/zainjo-logstream
sudo ln -s /etc/nginx/sites-available/zainjo-logstream \
           /etc/nginx/sites-enabled/zainjo-logstream
sudo nginx -t && sudo systemctl reload nginx

# ── Systemd service ──────────────────────────────────────────
sudo cp deployment/syslog-collector.service \
    /etc/systemd/system/zainjo-logstream.service
sudo chown -R logstream:logstream /opt/zainjo-logstream /var/log/zainjo-logstream \
    /data/syslog /etc/zainjo-logstream
sudo systemctl daemon-reload
sudo systemctl enable --now zainjo-logstream
```

---

## Configuration

Edit `/etc/zainjo-logstream/config.yaml` after installation.

Key settings:

| Setting | Default | Description |
|---------|---------|-------------|
| `syslog_port` | `1514` | UDP/TCP port for syslog reception |
| `syslog_workers` | `8` | Number of async log processor workers |
| `storage_path` | `/data/syslog` | Root directory for flat-file log storage |
| `retention_days` | `90` | Days to keep raw log files before deletion |
| `compress_after_days` | `7` | Days after which files are gzip-compressed |
| `siem_url` | `http://localhost:5000/api/logs` | SIEM endpoint for log forwarding |
| `siem_enabled` | `true` | Enable/disable SIEM forwarding |
| `siem_batch_size` | `100` | Logs per HTTP POST to SIEM |
| `secret_key` | — | JWT signing key — **must change in production!** |
| `access_token_expire_minutes` | `480` | Session timeout (8 hours) |

After editing config, restart the service:
```bash
sudo systemctl restart zainjo-logstream
```

---

## Adding Sources

### Via the UI

1. Log in to the dashboard (http://your-server)
2. Navigate to **Sources** → **Add Source**
3. Fill in:
   - **Source Name**: e.g. `Huawei-NCE-FAN`
   - **IP Address**: e.g. `10.x.x.x`
   - **Vendor**: Huawei / Nokia / Ericsson
   - **System Type**: NCE / U2020 / NetAct / ENM / etc.
   - **Protocol**: UDP / TCP / BOTH
   - **Port**: `1514`

### Via API

```bash
curl -s -X POST http://your-server/api/sources \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Huawei-NCE-FAN",
    "ip_address": "10.1.1.100",
    "vendor": "Huawei",
    "system_type": "NCE",
    "protocol": "UDP",
    "port": 1514,
    "enabled": true
  }'
```

### Configure the source device to send syslog

Point each NMS/EMS to send syslog to:
```
UDP/TCP  <this-server-ip>:1514
```

**Huawei NCE example:**
```
syslog host <this-server-ip> port 1514 facility local6
```

**Nokia NetAct / Ericsson ENM:**
Configure syslog forwarding via their respective alarm/event management GUIs to forward to `<this-server-ip>:1514`.

---

## Adding Filtering Rules

### Via the UI

1. Navigate to **Filter Rules** → **New Rule**
2. Select the **Source** this rule applies to
3. Set **Field** = `username`, **Match Type** = `exact`
4. After creating the rule, click to expand it and add blocked patterns

### Blocking specific users

Example — block `backupuser`, `vendor`, `testuser` on `Huawei-NCE-FAN`:

```bash
# 1. Get the source ID
SOURCE_ID=$(curl -s http://your-server/api/sources -H "Authorization: Bearer $TOKEN" \
  | python3 -c "import sys,json; data=json.load(sys.stdin); [print(s['id']) for s in data['items'] if s['name']=='Huawei-NCE-FAN']")

# 2. Create filter rule
RULE_ID=$(curl -s -X POST http://your-server/api/filters \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"Block Backup Users\", \"source_id\": \"$SOURCE_ID\",
       \"field\": \"username\", \"pattern_type\": \"exact\",
       \"action\": \"drop\", \"enabled\": true,
       \"patterns\": [\"backupuser\", \"vendor\", \"testuser\"]}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "Rule created: $RULE_ID"
```

### Adding more users to an existing rule

```bash
curl -X POST http://your-server/api/filters/$RULE_ID/users \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"pattern": "newblockeduser"}'
```

### Regex matching example

Block any user matching `vendor_.*` or `test_.*`:
```json
{
  "name": "Block Vendor and Test Users",
  "field": "username",
  "pattern_type": "regex",
  "patterns": ["vendor_.*", "test_.*", "backup.*"]
}
```

---

## Service Management

```bash
# Status
sudo systemctl status zainjo-logstream

# Start / Stop / Restart
sudo systemctl start   zainjo-logstream
sudo systemctl stop    zainjo-logstream
sudo systemctl restart zainjo-logstream

# Live logs
sudo journalctl -u zainjo-logstream -f

# Application log file
sudo tail -f /var/log/zainjo-logstream/app.log

# Nginx logs
sudo tail -f /var/log/nginx/zainjo-logstream.access.log
sudo tail -f /var/log/nginx/zainjo-logstream.error.log
```

---

## User Management

### Change admin password

1. Log in as admin → profile (top-left)
2. Or via API:

```bash
curl -s -X PATCH http://your-server/api/auth/users/$USER_ID \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"password": "NewSecurePassword123!"}'
```

### Create a viewer account

```bash
curl -s -X POST http://your-server/api/auth/users \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"username": "nocoperator", "password": "Password123!", "role": "viewer"}'
```

### Roles

| Role | Capabilities |
|------|-------------|
| `admin` | Full access: manage sources, filters, users, view all data |
| `viewer` | Read-only: view dashboard, search logs, view audit |

---

## Log Storage Structure

```
/data/syslog/
├── raw/
│   ├── huawei/
│   │   ├── 2024-01-15.log           # Current day (plain text)
│   │   ├── 2024-01-08.log.gz        # Compressed (>7 days)
│   │   └── ...
│   ├── nokia/
│   └── ericsson/
├── archive/
│   ├── huawei/
│   │   └── 2023-11-01.log.gz       # Archived older files
│   └── ...
├── processed/
└── failed/
    └── siem_failed_20240115T120000.jsonl  # Failed SIEM forwards
```

The cleanup scheduler runs every 24 hours:
- Compresses files older than `compress_after_days` (default: 7)
- Deletes files older than `retention_days` (default: 90)

---

## SIEM Integration

The forwarder POSTs batches to `siem_url` with this JSON payload:

```json
{
  "logs": [
    {
      "source": "Huawei-NCE-FAN",
      "vendor": "huawei",
      "timestamp": "2024-01-15T10:30:00Z",
      "username": "admin",
      "severity": "INFO",
      "raw_message": "<134>Jan 15 10:30:00 nce-fan sshd: ...",
      "parsed_fields": {
        "username": "admin",
        "operation": "login",
        "result": "success"
      }
    }
  ],
  "count": 1
}
```

**Retry behavior:** 3 attempts with exponential backoff (2s → 4s → 8s). Failed batches are saved to `/data/syslog/failed/` as JSONL files — no logs are lost.

---

## Troubleshooting

### Service fails to start
```bash
sudo journalctl -u zainjo-logstream -n 100 --no-pager
```

Common causes:
- **Database connection failed**: Check `database_url` in config.yaml, verify PostgreSQL is running
- **Port 1514 in use**: `sudo ss -tulnp | grep 1514`
- **Permission denied**: `sudo chown -R logstream:logstream /opt/zainjo-logstream /data/syslog`

### Logs not appearing in the dashboard
1. Verify the source device is sending to the correct IP and port 1514
2. Check if the source is registered and enabled in **Sources**
3. Check the app log: `sudo tail -f /var/log/zainjo-logstream/app.log`
4. Test with netcat: `echo "<134>Test message" | nc -u <server-ip> 1514`

### SIEM forwarding failures
- Failed batches are saved to `/data/syslog/failed/` — they can be replayed manually
- Check SIEM is running on port 5000: `curl http://localhost:5000/api/logs`
- Adjust `siem_retry_attempts` and `siem_timeout` in config

### Database disk space
```bash
sudo -u postgres psql -d logstream -c "\l+"
# Check table sizes
sudo -u postgres psql -d logstream -c "
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
FROM pg_tables WHERE schemaname='public' ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
```

For very high volumes, consider PostgreSQL table partitioning on `received_at`. See [PostgreSQL docs on partitioning](https://www.postgresql.org/docs/current/ddl-partitioning.html).

### High CPU on the VM
- Reduce `syslog_workers` in config (default 8)
- Enable `siem_enabled: false` temporarily if SIEM is slow

---

## Performance Tuning

For millions of logs/day on the provided 32 vCPU / 62 GB VM:

**config.yaml:**
```yaml
syslog_workers: 16          # Increase processor workers
syslog_queue_size: 500000   # Larger in-memory queue
siem_batch_size: 500        # Larger SIEM batches
```

**PostgreSQL tuning** (`/etc/postgresql/*/main/postgresql.conf`):
```
shared_buffers = 8GB
work_mem = 64MB
maintenance_work_mem = 2GB
max_connections = 100
wal_level = minimal
synchronous_commit = off     # Faster writes, slightly less durable
checkpoint_completion_target = 0.9
```

**Partition syslog_entries by month** (for > 10M rows/day):
```sql
-- Consult the PostgreSQL partitioning guide for this migration
```

---

## API Reference

Interactive API docs available at: `http://your-server/api/docs`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/login` | POST | Authenticate, get JWT token |
| `/api/auth/me` | GET | Current user info |
| `/api/dashboard/stats` | GET | Overview statistics |
| `/api/logs` | GET | Search syslog entries |
| `/api/logs/{id}` | GET | Get single log entry |
| `/api/sources` | GET/POST | List/create sources |
| `/api/sources/{id}` | PATCH/DELETE | Update/delete source |
| `/api/filters` | GET/POST | List/create filter rules |
| `/api/filters/{id}/users` | POST | Add blocked user/pattern |
| `/api/filters/{id}/users/{uid}` | DELETE | Remove blocked user |
| `/api/audit` | GET | Search audit logs |

---

## Stack

| Component | Technology |
|-----------|-----------|
| Backend   | Python 3.12 + FastAPI + uvicorn (uvloop) |
| Database  | PostgreSQL + SQLAlchemy 2.0 (async) + Alembic |
| Syslog    | asyncio UDP/TCP listeners (native Python) |
| Parsers   | Vendor-specific regex parsers (Huawei, Nokia, Ericsson) |
| SIEM Fwd  | httpx async HTTP client with retry queue |
| Cleanup   | APScheduler (async, in-process) |
| Frontend  | React 18 + Vite + TypeScript + Tailwind CSS |
| Charts    | Recharts |
| Proxy     | Nginx |
| Service   | systemd |

---

*ZainJo LogStream — Built for Telecom NOC environments. Internal use only.*
