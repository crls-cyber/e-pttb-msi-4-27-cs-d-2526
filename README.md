# 🛡️ Pentest Toolbox — M1 Cybersecurity Project

**Automated Penetration Testing Platform**

[![License](https://img.shields.io/badge/license-CC--BY--NC--ND--4.0-lightgrey.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/docker-24.0+-blue.svg)](https://www.docker.com/)
[![Status](https://img.shields.io/badge/status-v2.0%20complete-success.svg)]()

> **Academic Project** — M1 Cybersecurity, Sup de Vinci (2025-2026)
> Automated modular toolbox for penetration testing with RBAC, data-driven Pivot Chains, professional reporting, and Docker orchestration.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Plugins](#plugins)
- [Documentation](#documentation)
- [Security](#security)
- [Legal Notice](#legal-notice)
- [License](#license)

---

## 🎯 Overview

**Pentest Toolbox v2** is a modular penetration testing platform designed to:
- ✅ **Automate** reconnaissance, scanning and exploitation phases
- ✅ **Reduce** pentest time through orchestrated workflows and data-driven Pivot Chains
- ✅ **Standardize** practices with reusable, auto-discovered plugins
- ✅ **Secure** access with RBAC (Admin, Analyst, Viewer) and zero-trust scope enforcement
- ✅ **Generate** professional reports (HTML, PDF, CSV)

**Target users:** Security analysts, pentesters, SOC teams, academic researchers.

---

## ✨ Features

### 🔌 13 Integrated Tools

**Flux A — Automated Docker Plugins (8)**

| Plugin | Phase | Capability |
|--------|-------|------------|
| **Nmap** | Reconnaissance | Network scanning, port & service detection |
| **Nuclei** | Vulnerabilities | CVE detection (5000+ templates) |
| **SQLmap** | Exploitation | SQL injection automation |
| **Hydra** | Credential Access | Brute-force (SSH, FTP, SMB, MySQL, RDP...) |
| **Subfinder** | OSINT | Passive subdomain enumeration |
| **theHarvester** | OSINT | Email, host, IP collection via search engines |
| **WhatWeb** | Fingerprinting | Web technology identification |
| **ZAP (OWASP)** | Web Audit | Active web vulnerability scan (XSS, CSRF...) |

**Flux C — Upload Parsers (5)**

| Tool | Import Format | Phase |
|------|--------------|-------|
| **Metasploit** | Log (.log) | Exploitation / Post-exploitation |
| **Burp Suite** | XML export (.xml) | Advanced web audit |
| **Wireshark** | PCAP (.pcap) | Network analysis / Forensics |
| **Aircrack-ng** | Log (.txt) | Wi-Fi audit |
| **Ettercap** | Log (.txt) | Man-in-the-Middle |

### 🔄 7 Sequential Workflows

One-click chains on a fixed target:

| Workflow | Chain |
|----------|-------|
| Recon-to-Exploit | Nmap → Nuclei → Hydra |
| Web Pentest Advanced | Nmap → Nuclei → SQLmap |
| Web App Audit | WhatWeb → ZAP → SQLmap |
| Network Bruteforce | Nmap → Hydra |
| OSINT Reconnaissance | theHarvester → Subfinder |
| Quick Vuln Scan | Nmap → Nuclei |
| Full External Recon | Subfinder → theHarvester → Nmap → WhatWeb |

### 🔀 3 Data-Driven Pivot Chains

Unlike sequential workflows, Pivot Chains dynamically create follow-up jobs based on the actual results of the previous step:

| Pivot Chain | Logic | Tested Result |
|-------------|-------|--------------|
| **Network Pivot Discovery** | Nmap (CIDR) → [per discovered host] → Nuclei + WhatWeb | 4 hosts found, 8 jobs created dynamically ✅ |
| **Credential Access Discovery** | Nmap (auth ports) → [per open service] → Hydra | 10 auth services found, 10 Hydra jobs launched precisely ✅ |
| **Exploitation Readiness Report** | Nmap + Nuclei → [findings analysis] → Metasploit recommendations | vsftpd 2.3.4 backdoor identified with precise module, 15+ CVE hints ✅ |

### 📊 Professional Reporting

- **Per-job reports** — HTML / PDF with CVSS score, CVE ID, description, remediation
- **Global report** — all findings across all completed jobs
- **Custom report** — filtered by target, plugin and/or date range
- **CSV export** — for external analysis

### 🔐 Built-in Security

- **Authentication** — Flask-Login, hashed passwords (Werkzeug)
- **RBAC** — 3 roles enforced server-side (Admin, Analyst, Viewer)
- **Scope Enforcement** — Zero-trust: no scan without prior authorization in Targets registry
- **Audit Logs** — all sensitive actions tracked (login, target/user creation, workflow launches)
- **Methodological independence** — analysts see only their own jobs/findings

---

## 🏛️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              USERS (Analysts)                               │
│              Web Interface EN/FR (Delta OS theme)           │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────────────────┐
         │   UI + API (Flask)    │
         │   Port 5000           │
         │   Auth + RBAC         │
         │   13 dedicated pages  │
         └───────────┬───────────┘
                     │
        ┌────────────┴────────────┐
        ▼                         ▼
┌───────────────┐         ┌──────────────┐
│  PostgreSQL   │         │    Redis     │
│  Jobs         │         │   Broker     │
│  Findings     │         │   Celery     │
│  Users        │         └──────┬───────┘
│  Audit logs   │                │
└───────────────┘                ▼
                    ┌─────────────────────────┐
                    │   Celery Worker          │
                    │   4 parallel processes   │
                    └──────────┬──────────────┘
                               │
              ┌────────────────┴────────────────┐
              ▼                                  ▼
   ┌─────────────────────┐          ┌──────────────────────┐
   │  Flux A : Docker    │          │  Flux C : Upload     │
   │  8 automated tools  │          │  5 external parsers  │
   └──────────┬──────────┘          └──────────────────────┘
              ▼
   ┌─────────────────────┐
   │       MinIO          │
   │  Artifacts storage   │
   │  (S3-compatible)     │
   └─────────────────────┘
```

**Key design decisions:**
- **Celery** over threading — true async, retry, monitoring
- **MinIO** over filesystem — S3-compatible, cloud-ready
- **Flask** — recommended by project spec, mature ecosystem
- **Plugin auto-discovery** — add a tool without touching the core

---

## 🧰 Tech Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Language | Python | 3.11+ |
| Web Framework | Flask | 3.0+ |
| ORM | SQLAlchemy | 2.0+ |
| Async Jobs | Celery | 5.3+ |
| Message Broker | Redis | 7.0+ |
| Database | PostgreSQL | 15+ |
| Object Storage | MinIO | Latest |
| Containers | Docker Compose | V2 |
| Dependency Mgmt | Poetry | 1.7+ |
| PDF Generation | WeasyPrint | 62.0+ |
| CI/CD | GitHub Actions | — |

---

## 🚀 Quick Start

### Prerequisites

- **OS:** Kali Linux 2026+ (or Debian/Ubuntu 22.04+)
- **Docker:** 24.0+
- **Docker Compose:** V2
- **RAM:** 4GB minimum, 8GB recommended
- **Disk:** 20GB minimum

### Installation

```bash
# 1. Clone repository
git clone https://github.com/crls-cyber/e-pttb-msi-4-27-cs-d-2526.git
cd e-pttb-msi-4-27-cs-d-2526

# 2. Configure environment
cp deploy/.env.example deploy/.env
nano deploy/.env  # Edit passwords and secrets

# 3. Start all services
docker compose up -d

# 4. Wait for services to initialize (~30 seconds)
sleep 30

# 5. Initialize database
docker compose exec api python scripts/init_db.py

# 6. Create admin user
docker compose exec api python scripts/create_user.py \
  --username admin \
  --password YourStrongPassword \
  --email admin@toolbox.local \
  --role admin

# 7. Open web interface
firefox http://localhost:5000
```

### After Installation

1. Log in as `admin`
2. Go to **Targets** → add your authorized targets (IP, CIDR, domain)
3. Go to **Workflows** or **Pivot Chains** → launch your first scan
4. Results appear in **Jobs** → **Findings**

---

## 🔌 Plugins

### Automated Docker Plugins (8)

| Plugin | Status | Notes |
|--------|--------|-------|
| Nmap | ✅ Operational | Service detection, CIDR ranges supported |
| Nuclei | ✅ Operational | 5000+ CVE templates |
| SQLmap | ✅ Operational | Optional sqli_url parameter |
| Hydra | ✅ Operational | Userlist as Python list supported |
| Subfinder | ✅ Operational | Domain names only (not IPs) |
| theHarvester | ✅ Operational | Timeout on rate-limited sources (known) |
| WhatWeb | ✅ Operational | |
| ZAP (OWASP) | ⚠️ Partial | Spider timeout bug identified, fix planned |

### Upload Parsers (5)

| Tool | Status |
|------|--------|
| Metasploit | ✅ Operational |
| Burp Suite | ✅ Operational |
| Wireshark | ✅ Operational |
| Aircrack-ng | ✅ Operational |
| Ettercap | ✅ Operational |

### Adding a Plugin

Each plugin extends `PluginBase` and implements three methods:
- `validate_config()` — parameter validation
- `run()` — tool execution via subprocess
- `parse_output()` — raw output → structured Findings

Plugins are **auto-discovered** at startup — no core modification needed.

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [QUICKSTART_v3.md](QUICKSTART_v3.md) | Step-by-step setup guide |
| [PLAN_DEVELOPPEMENT_v3.md](PLAN_DEVELOPPEMENT_v3.md) | Development plan |
| [CHECKLIST_PRELANCEMENT_v3.md](CHECKLIST_PRELANCEMENT_v3.md) | Pre-launch checklist |
| [docs/FUTURE_IMPROVEMENTS.md](docs/FUTURE_IMPROVEMENTS.md) | Roadmap and planned features |
| [architecture_pentest_toolbox_v6_1.md](architecture_pentest_toolbox_v6_1.md) | Detailed architecture |

---

## 🔐 Security

### Built-in Controls

- ✅ Password hashing (Werkzeug)
- ✅ RBAC enforced server-side
- ✅ Zero-trust scope enforcement (no unauthorized scans)
- ✅ Audit trail (all sensitive actions logged)
- ✅ Session security (Flask-Login signed cookies)

### Deployment Recommendation

This toolbox is designed for **dedicated mission machines** — one machine per engagement. Data stays local by default. No cloud dependencies required.

### Known Limitation

ZAP spider (`_wait_for_spider()`) lacks a timeout parameter — can block indefinitely on certain targets. Fix planned. Workaround: restart worker if blocked.

---

## ⚖️ Legal Notice

**This project is an academic research tool.**

**Article 323-1 of the French Penal Code:**
> Unauthorized access to an automated data processing system is punishable by two years' imprisonment and a fine of €60,000.

**Use this toolbox ONLY on:**
- ✅ Your own systems
- ✅ Systems with explicit written authorization
- ✅ Authorized lab targets (Metasploitable2, DVWA, etc.)

**❌ NEVER scan systems without prior written authorization.**

The authors assume **no responsibility** for illegal use of this tool.

---

## 📄 License

This project is licensed under **CC BY-NC-ND 4.0**
(Attribution — Non Commercial — No Derivatives)

See [LICENSE](LICENSE) for full terms.

---

## 🎓 Academic Context

**Institution:** Sup de Vinci — M1 Cybersecurity
**Period:** December 2025 – June 2026
**Team:** Carlos (@crls-cyber), Emeric (@freezy-ted), Antoine (@ItsJinmaa), Elsy (@nker-svg)

---

**Version:** v2.0
**Last Updated:** June 26, 2026
**Status:** ✅ Complete
