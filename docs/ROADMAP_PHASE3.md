# 🚀 ROADMAP Phase 3 — ToolBox Pentest M1

**Version :** v1.0.0-mvp (current state)  
**Target Version :** v2.0.0 (Phase 3 completion)  
**Period :** June 8-22, 2026 (2 weeks)  
**Team :** 4 members (M1 Cybersécurité)

---

## 📋 Table des matières

- [Phase 3 Overview](#phase-3-overview)
- [New Plugins](#new-plugins)
- [Infrastructure Improvements](#infrastructure-improvements)
- [Advanced Features](#advanced-features)
- [CI/CD Pipeline](#cicd-pipeline)
- [Production Deployment](#production-deployment)
- [Future Vision](#future-vision)

---

## 🎯 Phase 3 Overview

### Current State (End of Phase 1 - MVP)

**Delivered (May 17, 2026):**
- ✅ 5 plugins operational (Nmap, Nuclei, SQLmap, theHarvester, Hydra)
- ✅ 2 external parsers (Wireshark, Metasploit)
- ✅ Job orchestration with Celery
- ✅ Web UI with authentication + RBAC
- ✅ HTML/PDF/CSV reporting
- ✅ Docker Compose infrastructure
- ✅ Complete documentation (7 docs)

**Metrics:**
- 17+ API endpoints
- 9 UI templates
- 5 plugins automated
- ~98% CDC compliance

---

### Phase 3 Goals (June 8-22)

**Objectives:**
1. ✅ Add 3 new plugins (Aircrack-ng, Ettercap, Maltego)
2. ✅ HTTPS setup with Traefik reverse proxy
3. ✅ CI/CD pipeline with GitHub Actions
4. ✅ Advanced dashboards with real-time metrics
5. ✅ Production-ready deployment guide
6. ✅ Final demo video + presentation slides

**Target:** Production-ready toolbox for real pentest operations

---

## 🔌 New Plugins

### 1. Aircrack-ng (WiFi Security)

**Purpose:** Automated WiFi penetration testing

**Capabilities:**
- Capture WPA/WPA2 handshakes
- Dictionary attack on captured handshakes
- WEP cracking
- Deauthentication attacks

**Implementation:**

```python
# plugins/aircrack/plugin.py
class AircrackPlugin(PluginBase):
    name = "aircrack"
    version = "1.0"
    capabilities = ["network_scan", "wifi_attack"]
    
    def run(self, config):
        interface = config['interface']  # e.g., wlan0mon
        target_bssid = config['bssid']
        wordlist = config.get('wordlist', '/wordlists/rockyou.txt')
        
        # Capture handshake
        subprocess.run([
            'airodump-ng',
            '--bssid', target_bssid,
            '--channel', config['channel'],
            '--write', f'/tmp/capture_{job_id}',
            interface
        ], timeout=300)
        
        # Crack with wordlist
        result = subprocess.run([
            'aircrack-ng',
            '-w', wordlist,
            f'/tmp/capture_{job_id}-01.cap'
        ], capture_output=True, text=True)
        
        # Parse key if found
        if "KEY FOUND" in result.stdout:
            key = extract_key(result.stdout)
            return Finding(
                title=f"WiFi Key Found: {target_bssid}",
                severity="critical",
                description=f"WPA2 key cracked: {key}"
            )
```

**Docker Requirements:**
- Wireless adapter with monitor mode support
- `--privileged` flag for Docker container
- aircrack-ng suite installed

**Use Cases:**
- WiFi security audits
- Wireless penetration testing
- Rogue AP detection

**Priority:** Medium (Phase 3 Week 1)

---

### 2. Ettercap (MITM Attacks)

**Purpose:** Man-in-the-middle attacks and network sniffing

**Capabilities:**
- ARP spoofing
- DNS spoofing
- SSL stripping
- Password sniffing (HTTP, FTP, Telnet)
- Traffic interception and modification

**Implementation:**

```python
# plugins/ettercap/plugin.py
class EttercapPlugin(PluginBase):
    name = "ettercap"
    version = "1.0"
    capabilities = ["network_scan", "mitm_attack"]
    
    def run(self, config):
        target1 = config['target1']  # Gateway
        target2 = config['target2']  # Victim
        interface = config.get('interface', 'eth0')
        
        # Launch ARP spoofing MITM
        result = subprocess.run([
            'ettercap',
            '-T',  # Text mode
            '-M', 'arp:remote',  # ARP poisoning
            f'/{target1}//',
            f'/{target2}//',
            '-i', interface
        ], capture_output=True, text=True, timeout=300)
        
        # Parse intercepted credentials
        findings = parse_ettercap_output(result.stdout)
        return findings
```

**Security Warnings:**
- ⚠️ MITM attacks are HIGHLY ILLEGAL without authorization
- ⚠️ Use ONLY in isolated lab environment
- ⚠️ Similar warning interface to Hydra plugin

**Use Cases:**
- Network security audits
- Protocol analysis
- SSL/TLS vulnerability testing

**Priority:** Medium (Phase 3 Week 1)

---

### 3. Maltego (OSINT & Reconnaissance)

**Purpose:** Advanced OSINT and relationship mapping

**Capabilities:**
- Domain reconnaissance
- Social network analysis
- Email harvesting
- Infrastructure mapping
- Visual relationship graphs

**Implementation:**

```python
# plugins/maltego/plugin.py
class MaltegoPlugin(PluginBase):
    name = "maltego"
    version = "1.0"
    capabilities = ["osint", "recon"]
    
    def run(self, config):
        target = config['target']  # Domain or person
        
        # Use Maltego CLI (maltego-cli)
        result = subprocess.run([
            'maltego-cli',
            '--transform', 'toEmailAddress',
            '--entity', f'Domain:{target}'
        ], capture_output=True, text=True)
        
        # Parse Maltego XML output
        emails = parse_maltego_xml(result.stdout)
        
        findings = []
        for email in emails:
            findings.append(Finding(
                title=f"Email discovered: {email}",
                severity="info",
                description=f"Public email address found: {email}"
            ))
        
        return findings
```

**Alternative:** Use Maltego API instead of CLI

**Use Cases:**
- Corporate reconnaissance
- Social engineering prep
- Threat intelligence gathering

**Priority:** Low (Phase 3 Week 2, if time allows)

---

## 🏗️ Infrastructure Improvements

### 1. HTTPS with Traefik

**Current:** HTTP only (port 5000)

**Target:** HTTPS with automatic Let's Encrypt certificates

**Implementation:**

```yaml
# docker-compose.yml (Phase 3)
services:
  traefik:
    image: traefik:v2.10
    command:
      - "--api.insecure=true"
      - "--providers.docker=true"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.email=admin@toolbox.local"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./letsencrypt:/letsencrypt

  api:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.api.rule=Host(`toolbox.example.com`)"
      - "traefik.http.routers.api.entrypoints=websecure"
      - "traefik.http.routers.api.tls.certresolver=letsencrypt"
```

**Benefits:**
- ✅ Encrypted communication (TLS 1.3)
- ✅ Secure session cookies
- ✅ Automatic certificate renewal
- ✅ Production-ready security

**Priority:** High (Phase 3 Week 1)

---

### 2. Multi-Worker Scaling

**Current:** 1 Celery worker

**Target:** 4 parallel workers

```bash
# Scale workers
docker compose up -d --scale worker=4

# Verify
docker compose ps
# Should show: worker_1, worker_2, worker_3, worker_4
```

**Benefits:**
- ✅ 4x faster job execution
- ✅ Parallel scans (Nmap + Nuclei + SQLmap simultaneously)
- ✅ Better resource utilization

**Priority:** High (Phase 3 Week 1)

---

### 3. PostgreSQL Replication

**Current:** Single PostgreSQL instance

**Target:** 1 master + 2 read replicas

**Benefits:**
- ✅ High availability
- ✅ Read query distribution
- ✅ Disaster recovery

**Implementation:** PostgreSQL streaming replication

**Priority:** Low (nice-to-have for demo)

---

### 4. MinIO Distributed Mode

**Current:** Single MinIO node

**Target:** 4-node MinIO cluster (erasure coding)

**Benefits:**
- ✅ Data redundancy
- ✅ High availability
- ✅ Automatic healing

**Priority:** Low (overkill for MVP demo)

---

## 🎨 Advanced Features

### 1. WebSocket Real-Time Progress

**Current:** Polling `/api/jobs/{id}` for status

**Target:** WebSocket streaming of job progress

```javascript
// UI real-time updates
const ws = new WebSocket('ws://localhost:5000/ws/jobs/123');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  updateProgressBar(data.percentage);
  updateLogs(data.log_line);
};
```

**Benefits:**
- ✅ Real-time progress bars
- ✅ Live log streaming
- ✅ Better UX

**Priority:** Medium (Phase 3 Week 2)

---

### 2. Advanced Dashboards

**Current:** Basic stats on dashboard

**Target:** Interactive charts with Chart.js/D3.js

**Features:**
- 📊 Findings by severity (pie chart)
- 📈 Scans over time (line chart)
- 🔥 Top vulnerabilities (bar chart)
- 🗺️ Attack surface map (network diagram)

**Priority:** Medium (Phase 3 Week 2)

---

### 3. Export to JIRA/ServiceNow

**Feature:** One-click export of findings to ticketing systems

```python
# Export findings to JIRA
@api.route('/api/findings/export/jira', methods=['POST'])
def export_to_jira():
    findings = get_findings_by_job(job_id)
    
    for finding in findings:
        jira_client.create_issue(
            project='SEC',
            summary=finding.title,
            description=finding.description,
            issuetype='Bug',
            priority=map_severity_to_jira(finding.severity)
        )
    
    return {"message": f"{len(findings)} issues created in JIRA"}
```

**Priority:** Low (Phase 3 Week 2, if time)

---

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

**File:** `.github/workflows/ci.yml`

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install Poetry
        run: curl -sSL https://install.python-poetry.org | python3 -
      
      - name: Install dependencies
        run: poetry install
      
      - name: Run tests
        run: poetry run pytest tests/ -v --cov=core --cov=plugins
      
      - name: Lint with flake8
        run: poetry run flake8 core/ plugins/
      
      - name: Security scan with bandit
        run: poetry run bandit -r core/ plugins/
  
  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Build Docker images
        run: |
          docker compose build
      
      - name: Push to Docker Hub (optional)
        run: |
          echo "${{ secrets.DOCKER_PASSWORD }}" | docker login -u "${{ secrets.DOCKER_USERNAME }}" --password-stdin
          docker compose push
```

**Benefits:**
- ✅ Automated testing on every push
- ✅ Code quality checks (flake8, bandit)
- ✅ Security scanning
- ✅ Automatic Docker builds

**Priority:** High (Phase 3 Week 1)

---

## 🚀 Production Deployment

### Azure VM Deployment (Demo)

**Objective:** Deploy toolbox on Azure for final demo

**Specs:**
- VM Size: Standard_D2s_v3 (2 vCPU, 8GB RAM)
- OS: Ubuntu 22.04 LTS
- Network: Public IP with NSG (ports 80, 443 only)
- Storage: 100GB SSD

**Deployment Script:**

```bash
#!/bin/bash
# deploy_azure.sh

# Install Docker
sudo apt update
sudo apt install -y docker.io docker-compose-v2

# Clone repository
git clone https://github.com/crls-cyber/pentest-toolbox-v2.git
cd pentest-toolbox-v2

# Configure .env (from Azure Key Vault)
az keyvault secret show --name toolbox-env --vault-name toolbox-secrets \
  --query value -o tsv > deploy/.env

# Start services
cd deploy
docker compose -f docker-compose.prod.yml up -d

# Configure Traefik with Let's Encrypt
# (certificates auto-generated for toolbox.example.com)
```

**Priority:** Medium (Phase 3 Week 2, for demo)

---

## 🔮 Future Vision (Beyond Phase 3)

### Version 3.0 (Hypothetical)

**AI-Powered Features:**
- 🤖 GPT-4 integration for vulnerability analysis
- 🤖 Automatic remediation suggestions
- 🤖 Natural language query interface ("Find all critical SQLi vulnerabilities")

**Advanced Automation:**
- 🔄 Self-healing exploits (retry with different payloads)
- 🔄 Adaptive scanning (adjust intensity based on IDS detection)
- 🔄 Automated report generation with executive summaries

**Enterprise Features:**
- 👥 Multi-tenancy (multiple organizations)
- 📊 Compliance reporting (PCI-DSS, ISO 27001)
- 🔗 Integration with SIEM (Splunk, ELK)
- 📱 Mobile app (iOS/Android)

**Community:**
- 🌍 Open-source plugin marketplace
- 🌍 Community-contributed templates
- 🌍 Public CVE database integration

---

## 📅 Phase 3 Timeline

### Week 1 (June 8-14)

**Monday-Tuesday:**
- ✅ Setup CI/CD pipeline (GitHub Actions)
- ✅ Add Aircrack-ng plugin
- ✅ Scale to 4 workers

**Wednesday-Thursday:**
- ✅ HTTPS setup with Traefik
- ✅ Add Ettercap plugin
- ✅ Advanced dashboards (Chart.js)

**Friday:**
- ✅ Integration testing
- ✅ Bug fixes

---

### Week 2 (June 15-22)

**Monday-Wednesday:**
- ✅ Production deployment guide
- ✅ WebSocket real-time progress
- ✅ Maltego plugin (if time)

**Thursday:**
- ✅ Final testing
- ✅ Performance benchmarks
- ✅ Security audit

**Friday:**
- ✅ Demo video recording (10 minutes)
- ✅ Presentation slides
- ✅ Final documentation review

**Weekend (June 21-22):**
- ✅ Rehearsal
- ✅ Final polishing

---

## 🎯 Success Metrics

| Metric | Current (MVP) | Target (Phase 3) |
|--------|---------------|------------------|
| **Plugins** | 5 | 8+ |
| **Test Coverage** | 40% | 85%+ |
| **Deployment** | Docker Compose | Azure VM + HTTPS |
| **CI/CD** | None | GitHub Actions |
| **Documentation** | 7 docs | 10+ docs |
| **Performance** | 1 worker | 4 workers |
| **Security** | HTTP | HTTPS (TLS 1.3) |

---

**Version:** v1.0.0-mvp (current)  
**Target Version:** v2.0.0 (Phase 3 complete)  
**Last Updated:** 14 mai 2026  
**Maintainer:** Carlos + 3 team members (M1 Cybersécurité)
