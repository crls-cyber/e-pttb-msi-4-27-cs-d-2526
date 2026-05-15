# ToolBox M1 Credentials

**Created:** May 8-9, 2026  
**Last updated:** May 15, 2026

---

## User Accounts

| Service | Username | Password |
|---------|----------|----------|
| Flask Admin | admin | Test123! |

---

## Services

| Service | User | Password |
|---------|------|----------|
| PostgreSQL | pentest | ToolBox2026!PostgreSQL |
| MinIO | admin | ToolBox2026!MinIO |

---

## Encryption Keys

- **SECRET_KEY:** Stored in `.env` (do not commit)
- **FERNET_KEY:** Stored in `.env` (do not commit)

---

## Network Connections

**Service Endpoints:**
- **Flask API:** http://localhost:5000
- **PostgreSQL:** localhost:5432 (from Kali) / postgres:5432 (from Docker)
- **Redis:** localhost:6379 (from Kali) / redis:6379 (from Docker)
- **MinIO Console:** http://localhost:9001

---

## Metasploit RPC (msfrpcd)

| Parameter | Value | Notes |
|-----------|-------|-------|
| Host | Kali IP on target network | Adapt to your network config |
| Port | 55553 | Default msfrpcd port |
| Password | msf | Configured at startup |

**Start command:**
```bash
msfrpcd -P msf -S -a 0.0.0.0 &
```

**Verification:**
```bash
netstat -tulnp | grep 55553
# Should listen on 0.0.0.0:55553
```

**Plugin configuration example:**
```json
{
  "msf_host": "192.168.x.x",
  "msf_port": 55553,
  "msf_password": "msf"
}
```

---

## Test Targets

| Machine | Role | Notes |
|---------|------|-------|
| WebSRV | Debian web server | Vulnerable web app (Apache + SSH) |
| WS22 | Windows Server 2022 | Active Directory Domain Controller |
| Metasploitable2 | Intentionally vulnerable VM | Multi-service exploitation target |
| DVWA | Docker container | Included in docker-compose.yml (localhost:8080) |

**Network Configuration:**
- Adapt IP addresses according to your VMware network setup (Host-only or NAT)
- Configure `msf_host` in Metasploit plugin to match your Kali IP on the target network
- See `MY_LAB_CONFIG.md` for your personal network topology (not committed to Git)

---

## ⚠️ IMPORTANT

- **NEVER commit** the `.env` file to Git
- **NEVER commit** `MY_LAB_CONFIG.md` (personal network details)
- This CREDENTIALS.md file is safe to commit (generic configuration)
- For internal use only (academic project)
- **LEGAL:** Only scan targets you own or have explicit written permission to test

