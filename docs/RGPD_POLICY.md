# 🔒 RGPD & Data Protection Policy — ToolBox Pentest M1

**Version :** v1.0.0-mvp  
**Date :** 14 mai 2026  
**Scope :** Lab environment (Host-Only network)

---

## 📋 Table des matières

- [Context & Applicability](#context--applicability)
- [Data Collection](#data-collection)
- [Data Storage](#data-storage)
- [Data Retention](#data-retention)
- [User Rights](#user-rights)
- [Security Measures](#security-measures)
- [Incident Response](#incident-response)
- [Legal Framework](#legal-framework)

---

## 🎯 Context & Applicability

### Purpose

This document defines the **data protection policy** for the ToolBox Pentest M1 project, ensuring compliance with:

- **RGPD** (Règlement Général sur la Protection des Données)
- **GDPR** (General Data Protection Regulation)
- French cybersecurity regulations

### Scope

**This policy applies to:**
- ✅ Lab environments (academic project, isolated network)
- ✅ Internal testing on controlled VMs (Metasploitable2, WebSRV, WS22)
- ✅ User data within the toolbox (accounts, jobs, findings)

**This policy does NOT apply to:**
- ❌ Production pentesting (requires separate legal framework)
- ❌ Client data (no real client data in MVP)
- ❌ Third-party SaaS data (all data is self-hosted)

---

## 📊 Data Collection

### Personal Data Collected

| Data Type | Purpose | Legal Basis | Retention |
|-----------|---------|-------------|-----------|
| **Username** | Authentication | Contract/Consent | Until account deletion |
| **Email** | Account recovery, notifications | Contract/Consent | Until account deletion |
| **Password hash** | Authentication | Contract/Consent | Until account deletion |
| **IP address** | Audit logging, security | Legitimate interest | 90 days |
| **Session cookies** | Authentication state | Contract | Session duration |

### Technical Data Collected

| Data Type | Purpose | Storage |
|-----------|---------|---------|
| **Scan targets** (IPs, domains) | Job execution | PostgreSQL (`jobs.config`) |
| **Findings** (vulnerabilities) | Pentest results | PostgreSQL (`findings`) |
| **Artifacts** (XML, PCAP, logs) | Evidence storage | MinIO S3 buckets |
| **Audit logs** (user actions) | Security monitoring | PostgreSQL (`audit_logs`) |

### Data NOT Collected

- ❌ Biometric data
- ❌ Health data
- ❌ Financial data
- ❌ Geolocation (beyond IP address)
- ❌ Behavioral tracking (no analytics, no cookies beyond auth)

---

## 🗄️ Data Storage

### Storage Locations

**All data is stored locally within the lab environment:**

| Component | Technology | Location | Encryption |
|-----------|------------|----------|------------|
| **User accounts** | PostgreSQL | `postgres` container | Bcrypt passwords |
| **Jobs & findings** | PostgreSQL | `postgres` container | Database-level encryption (optional) |
| **Artifacts** | MinIO S3 | `minio` container | Server-side encryption (optional) |
| **Audit logs** | PostgreSQL | `postgres` container | None (structured logs) |
| **Secrets** | Environment variables | `.env` file (not in Git) | Fernet encryption |

### Geographic Location

**Data residency:** All data stays within the **physical machine** hosting the Kali VM (Host-Only network).

**No cloud storage:** No data leaves the local network.

---

## ⏳ Data Retention

### Retention Periods

| Data Type | Retention Period | Rationale |
|-----------|------------------|-----------|
| **User accounts** | Until deletion by user or admin | Operational necessity |
| **Jobs** | 1 year (configurable) | Historical analysis |
| **Findings** | 1 year (configurable) | Audit trail |
| **Artifacts** | 1 year (configurable) | Evidence preservation |
| **Audit logs** | 90 days | Security monitoring |
| **Session cookies** | Session duration (max 24h) | Authentication state |

### Automated Deletion

**Planned for Phase 2:**

```bash
# Cron job to delete old data
0 2 * * 0 docker compose exec postgres psql -U pentest -c \
  "DELETE FROM jobs WHERE created_at < NOW() - INTERVAL '1 year';"
```

### Manual Deletion

**Admin can manually delete data via:**

```bash
# Delete specific job and related findings
docker compose exec api python scripts/delete_job.py --job-id <uuid>

# Delete user and all associated data
docker compose exec api python scripts/delete_user.py --username <user>
```

---

## 🙋 User Rights

### GDPR Rights

Users have the following rights under GDPR/RGPD:

#### 1. Right to Access (Article 15)

**Request:** "Show me all data you have about me"

**Implementation:**
```bash
# Export user data to JSON
curl http://localhost:5000/api/users/me/export -b cookies.txt > my_data.json
```

#### 2. Right to Rectification (Article 16)

**Request:** "Correct my email address"

**Implementation:** Edit via UI (`/profile`) or API (`PATCH /api/users/me`)

#### 3. Right to Erasure (Article 17)

**Request:** "Delete my account and all data"

**Implementation:**
```bash
# Full account deletion (GDPR-compliant)
curl -X DELETE http://localhost:5000/api/users/me -b cookies.txt
```

**What gets deleted:**
- User account
- All jobs created by user
- All findings from user's jobs
- All artifacts uploaded by user
- All audit logs related to user

#### 4. Right to Data Portability (Article 20)

**Request:** "Export my data in machine-readable format"

**Implementation:** Export endpoint returns JSON (already implemented above)

#### 5. Right to Object (Article 21)

**Not applicable** in this context (no automated decision-making, no profiling)

---

## 🔐 Security Measures

### Technical Measures

| Measure | Implementation | Status |
|---------|----------------|--------|
| **Password hashing** | Bcrypt (cost factor 12) | ✅ Implemented |
| **Secret encryption** | Fernet symmetric encryption | ✅ Implemented |
| **Session security** | Httponly cookies, secure flag (HTTPS) | ⚠️ HTTPS in Phase 3 |
| **RBAC** | Role-based access control (Admin, Analyst, Viewer) | ✅ Implemented |
| **Audit logging** | All sensitive actions logged | ✅ Implemented |
| **Network isolation** | Host-Only network (no Internet exposure) | ✅ Implemented |
| **Container isolation** | Docker network segmentation | ✅ Implemented |

### Organizational Measures

- ✅ **Access control:** Only authorized lab members can access the toolbox
- ✅ **Documentation:** This policy + architecture docs
- ✅ **Training:** Team aware of GDPR principles (M1 Cybersécurité)
- ✅ **Incident response plan:** See below

---

## 🚨 Incident Response

### Data Breach Procedure

**If a data breach occurs (e.g., unauthorized access, data leak):**

#### Step 1: Containment (0-4 hours)

1. **Identify scope:** What data was accessed/leaked?
2. **Isolate affected systems:** Shut down compromised containers
3. **Preserve evidence:** Take snapshots, save logs

```bash
# Emergency shutdown
docker compose down

# Preserve logs
docker compose logs > incident_$(date +%Y%m%d_%H%M%S).log

# Take VM snapshot
# (Via VMware interface)
```

#### Step 2: Assessment (4-24 hours)

1. **Determine impact:** How many users affected?
2. **Root cause analysis:** How did the breach occur?
3. **Legal obligations:** Must notify CNIL within 72 hours if high risk

#### Step 3: Notification (24-72 hours)

**If required by law:**
- Notify affected users via email
- Report to CNIL (Commission Nationale de l'Informatique et des Libertés)

**For academic project:**
- Notify project supervisor
- Document incident in `docs/INCIDENTS.md`

#### Step 4: Remediation

1. **Patch vulnerabilities**
2. **Reset passwords**
3. **Review access logs**
4. **Update security measures**

---

## ⚖️ Legal Framework

### Applicable Regulations

#### RGPD/GDPR (EU Regulation 2016/679)

**Key principles:**
- **Lawfulness, fairness, transparency** (Article 5.1.a)
- **Purpose limitation** (Article 5.1.b)
- **Data minimization** (Article 5.1.c)
- **Accuracy** (Article 5.1.d)
- **Storage limitation** (Article 5.1.e)
- **Integrity and confidentiality** (Article 5.1.f)
- **Accountability** (Article 5.2)

**Compliance status:** ✅ Compliant for lab use

#### French Data Protection Act (Loi Informatique et Libertés)

**Last updated:** August 20, 2004 (modified 2018)

**Key obligations:**
- Data controller must be identified (Carlos, M1 project lead)
- Users must consent to data processing
- Security measures must be proportionate

**Compliance status:** ✅ Compliant for academic project

#### Article 323-1 Code Pénal (Cybersecurity)

**Relevance:** This toolbox is used **only for authorized pentesting** (lab environment, controlled VMs).

**Legal protection:** All scans are performed on:
- ✅ Own machines (Metasploitable2, WebSRV, WS22)
- ✅ Isolated Host-Only network
- ❌ Never on production systems without explicit authorization

---

## 📝 Data Processing Register (RGPD Article 30)

### Processing Activities

| Activity | Purpose | Legal Basis | Data | Retention |
|----------|---------|-------------|------|-----------|
| **User authentication** | Access control | Contract | Username, email, password hash | Until deletion |
| **Job execution** | Pentest automation | Contract | Targets, configs, findings | 1 year |
| **Audit logging** | Security monitoring | Legitimate interest | IP, actions, timestamps | 90 days |
| **Artifact storage** | Evidence preservation | Contract | XML, PCAP, logs | 1 year |

---

## 🎓 Academic Context

### Exemptions & Clarifications

**This project is an academic/educational tool:**

- ✅ Used only in controlled lab environment
- ✅ No real client data processed
- ✅ No commercial use
- ✅ Data subjects are project team members (consent obtained)

**GDPR exemption for research (Article 89):**

Academic research benefits from certain derogations, but **we choose to apply full GDPR compliance** as a learning exercise.

---

## 📞 Contact

**Data Controller:** Carlos (M1 Cybersécurité)  
**Email:** [admin@toolbox.local](mailto:admin@toolbox.local)  
**Supervisor:** [Professeur responsable du projet]

**To exercise your rights or report an issue:**
- Open an issue on GitHub: `https://github.com/crls-cyber/pentest-toolbox-v2/issues`
- Contact the project supervisor

---

**Version:** v1.0.0-mvp  
**Last Updated:** 14 mai 2026  
**Next Review:** Phase 2 (before production deployment)
