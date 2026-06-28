# Quick Start Guide — Pentest ToolBox v2

> Get up and running in under 15 minutes.

---

## Prerequisites

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| OS | Kali Linux 2024+ or Debian/Ubuntu 22.04+ | Kali Linux 2026+ |
| RAM | 4 GB | 8 GB |
| Disk | 20 GB free | 50 GB free |
| Docker | 24.0+ | Latest |
| Docker Compose | V2 | Latest |

---

## Step 1 — Clone the repository

```bash
git clone https://github.com/crls-cyber/e-pttb-msi-4-27-cs-d-2526.git
cd e-pttb-msi-4-27-cs-d-2526
```

---

## Step 2 — Configure environment

```bash
cp deploy/.env.example deploy/.env
nano deploy/.env
```

Set strong passwords for all services. At minimum, change:

```env
POSTGRES_PASSWORD=YourStrongPassword
MINIO_ROOT_PASSWORD=YourStrongPassword
SECRET_KEY=YourRandomSecretKey
```

> **Never commit your `.env` file to Git.**

---

## Step 3 — Start all services

```bash
docker compose up -d
```

Wait ~30 seconds for all services to initialize, then verify:

```bash
docker compose ps
```

All 6 services should show **Up** :
- `api` — Flask web application (port 5000)
- `worker` — Celery async worker
- `postgres` — PostgreSQL database
- `redis` — Message broker
- `minio` — Artifact storage (port 9001)
- `dvwa` — Test target (port 8080)

---

## Step 4 — Initialize the database

```bash
docker compose exec api python scripts/init_db.py
```

---

## Step 5 — Create admin user

```bash
docker compose exec api python scripts/create_user.py \
  --username admin \
  --password YourAdminPassword \
  --email admin@toolbox.local \
  --role admin
```

---

## Step 6 — Open the interface

Open your browser at **http://localhost:5000** and log in with your admin credentials.

---

## First scan — 3 steps

### 1. Add an authorized target

Go to **Targets** → **Add Target**

```
Type:        IP
Value:       192.168.10.102    ← your Metasploitable2 IP
Description: Metasploitable2
Status:      Authorized
```

> No scan can be launched on an unauthorized target (zero-trust enforcement).

### 2. Launch a workflow

Go to **Workflows** → **Quick Vuln Scan**

```
Target: 192.168.10.102
```

Click **Launch** — the workflow runs Nmap then Nuclei asynchronously.

### 3. View results

Go to **Jobs** — watch the scan complete in real time.
Go to **Findings** — view discovered vulnerabilities with CVSS scores and remediation advice.

---

## Troubleshooting

### API or Worker won't start

```bash
docker compose logs api
docker compose logs worker
```

Most common cause: missing variables in `deploy/.env`.
Check that `POSTGRES_PASSWORD`, `MINIO_ROOT_PASSWORD` and `SECRET_KEY` are set.

### Can't reach scan targets

```bash
# From inside the worker container
docker compose exec worker ping 192.168.10.102
```

If unreachable, verify your network adapter is set to **Host-only** on both Kali and target VMs.

### Worker blocked (ZAP spider)

If the **Web App Audit** workflow hangs indefinitely:

```bash
docker compose restart worker
```

Known issue — fix planned. Use **Quick Vuln Scan** or **Web Pentest Advanced** instead.

---

## Next steps

- See `docs/LAB_CONFIG_EXAMPLE.md` for a recommended lab network setup
- See `docs/FUTURE_IMPROVEMENTS.md` for the feature roadmap
- See `docs/RGPD_POLICY.md` for data protection policy

---

*Pentest ToolBox v2 — M1 Cybersécurité, Sup de Vinci 2025-2026*
