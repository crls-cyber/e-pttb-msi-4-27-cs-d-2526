# 💾 Backup & Recovery Procedures — ToolBox Pentest M1

**Version :** v1.0.0-mvp  
**Date :** 14 mai 2026  
**Responsible :** Carlos (M1 Cybersécurité)

---

## 📋 Table des matières

- [Overview](#overview)
- [What to Backup](#what-to-backup)
- [Backup Procedures](#backup-procedures)
- [Recovery Procedures](#recovery-procedures)
- [Backup Schedule](#backup-schedule)
- [Storage Locations](#storage-locations)
- [Testing Backups](#testing-backups)

---

## 🎯 Overview

### Purpose

This document defines **backup and recovery procedures** for the ToolBox Pentest M1 project to ensure:

- ✅ Data protection against hardware failure
- ✅ Quick recovery from accidental deletion
- ✅ VM snapshot strategy for development safety
- ✅ Business continuity (even in academic context)

### Backup Types

| Type | Frequency | Retention | Recovery Time |
|------|-----------|-----------|---------------|
| **VM Snapshots** | Daily (dev), Weekly (stable) | 10 snapshots max | < 5 minutes |
| **PostgreSQL Dumps** | Daily | 30 days | < 10 minutes |
| **MinIO Artifacts** | Weekly | 30 days | < 30 minutes |
| **Code Repository** | Every commit | Forever (Git) | < 1 minute |
| **Configuration** | Before changes | 10 versions | < 1 minute |

---

## 📦 What to Backup

### Critical Data

| Component | Location | Criticality | Backup Method |
|-----------|----------|-------------|---------------|
| **Source code** | Git repository | 🔴 CRITICAL | Git push |
| **Database** | PostgreSQL container | 🔴 CRITICAL | pg_dump |
| **Artifacts** | MinIO container | 🟡 IMPORTANT | mc mirror |
| **.env secrets** | `deploy/.env` | 🔴 CRITICAL | Encrypted USB |
| **VM state** | VMware files | 🟡 IMPORTANT | VM snapshots |

### Non-Critical (Can Be Recreated)

- ❌ Docker images (can be rebuilt)
- ❌ Redis cache (temporary data)
- ❌ Application logs (can be regenerated)
- ❌ Celery task states (ephemeral)

---

## 🔧 Backup Procedures

### 1. VM Snapshots (VMware)

**Purpose:** Complete system state backup (development safety net)

**Frequency:**
- Daily during active development (J1-J10)
- Before major changes (plugin addition, schema migration)
- After each milestone (end of J4, J7, J10)

**Procedure:**

```bash
# Via VMware Workstation UI
# VM → Snapshot → Take Snapshot

# Name format: 0X_JY_Description
# Examples:
# - 05_J4_Nmap_Working
# - 06_J7_UI_Complete
# - 07_J10_MVP_Final

# Or via vmrun CLI (if available)
vmrun snapshot "/path/to/Kali.vmx" "08_J10_Complete"
```

**Retention:**
- Keep **last 10 snapshots**
- Delete old snapshots when reaching disk limit
- Always keep: J1, J4, J7, J10 (milestones)

**Storage:** VMware snapshot files (.vmdk, .vmem, .vmsn)

---

### 2. PostgreSQL Database Backup

**Purpose:** Protect user accounts, jobs, findings, audit logs

**Frequency:** Daily (automated via cron)

**Manual Backup:**

```bash
# One-time backup
docker compose exec postgres pg_dump -U pentest pentest_toolbox \
  > ~/Desktop/ToolBox_M1/backups/postgres_$(date +%Y%m%d_%H%M%S).sql

# Verify backup
ls -lh ~/Desktop/ToolBox_M1/backups/postgres_*.sql

# Test backup integrity (optional)
head -20 ~/Desktop/ToolBox_M1/backups/postgres_*.sql
# Should show PostgreSQL dump header
```

**Automated Backup (Cron Job):**

```bash
# Add to crontab (Phase 2)
crontab -e

# Daily backup at 2 AM
0 2 * * * cd ~/Desktop/ToolBox_M1/pentest-toolbox-v2 && \
  docker compose exec -T postgres pg_dump -U pentest pentest_toolbox \
  > ~/Desktop/ToolBox_M1/backups/postgres_$(date +\%Y\%m\%d).sql

# Keep only last 30 days
0 3 * * * find ~/Desktop/ToolBox_M1/backups -name "postgres_*.sql" -mtime +30 -delete
```

**Backup Size:** ~5-50MB (depending on data volume)

---

### 3. MinIO Artifacts Backup

**Purpose:** Protect scan artifacts (XML, PCAP, logs)

**Frequency:** Weekly or before critical operations

**Procedure:**

```bash
# Install MinIO client (mc)
docker compose exec minio mc alias set local \
  http://localhost:9000 $MINIO_ROOT_USER $MINIO_ROOT_PASSWORD

# Mirror artifacts bucket to local directory
docker compose exec minio mc mirror local/artifacts \
  /tmp/artifacts_backup

# Copy from container to host
docker compose cp minio:/tmp/artifacts_backup \
  ~/Desktop/ToolBox_M1/backups/minio_$(date +%Y%m%d)

# Compress to save space
tar -czf ~/Desktop/ToolBox_M1/backups/minio_$(date +%Y%m%d).tar.gz \
  ~/Desktop/ToolBox_M1/backups/minio_$(date +%Y%m%d)

# Clean up uncompressed
rm -rf ~/Desktop/ToolBox_M1/backups/minio_$(date +%Y%m%d)
```

**Backup Size:** ~100MB-1GB (depending on artifacts)

**Retention:** 30 days

---

### 4. Configuration Files Backup

**Purpose:** Protect `.env` secrets and Docker configurations

**Frequency:** Before any modification

**Procedure:**

```bash
# Create backup directory
mkdir -p ~/Desktop/ToolBox_M1/backups/config

# Backup .env (CRITICAL - contains secrets)
cp deploy/.env ~/Desktop/ToolBox_M1/backups/config/.env.$(date +%Y%m%d)

# Backup docker-compose.yml
cp deploy/docker-compose.yml \
  ~/Desktop/ToolBox_M1/backups/config/docker-compose.yml.$(date +%Y%m%d)

# Verify
ls -lh ~/Desktop/ToolBox_M1/backups/config/
```

**⚠️ SECURITY WARNING:**

`.env` contains **sensitive secrets** (passwords, encryption keys).

**Storage options:**
1. **Encrypted USB key** (recommended)
2. **Encrypted external drive** (VeraCrypt container)
3. **Password-protected archive:**

```bash
# Encrypt .env with GPG
gpg -c ~/Desktop/ToolBox_M1/backups/config/.env.$(date +%Y%m%d)
# This creates .env.YYYYMMDD.gpg

# Remove unencrypted version
rm ~/Desktop/ToolBox_M1/backups/config/.env.$(date +%Y%m%d)
```

**❌ NEVER:**
- Commit `.env` to Git
- Store `.env` in Dropbox/Google Drive unencrypted
- Email `.env` to anyone

---

### 5. Git Repository Backup

**Purpose:** Source code versioning and disaster recovery

**Frequency:** Every commit (automatic)

**Procedure:**

```bash
# Push to GitHub (primary backup)
git push origin main

# Optional: Push to secondary remote (GitLab, personal server)
git remote add backup git@gitlab.com:user/pentest-toolbox-backup.git
git push backup main
```

**Automatic:** Already handled by Git workflow

---

## 🔄 Recovery Procedures

### Scenario 1: Database Corruption

**Symptom:** PostgreSQL container won't start, or data is corrupted

**Recovery:**

```bash
# Stop all services
docker compose down

# Remove corrupted database volume
docker volume rm deploy_postgres_data

# Recreate database
docker compose up -d postgres
sleep 10

# Restore from latest backup
cat ~/Desktop/ToolBox_M1/backups/postgres_YYYYMMDD.sql | \
  docker compose exec -T postgres psql -U pentest pentest_toolbox

# Restart all services
docker compose up -d

# Verify
docker compose logs postgres | tail -20
curl http://localhost:5000/api/health
```

**Recovery Time:** ~10 minutes

---

### Scenario 2: Accidental File Deletion

**Symptom:** Deleted important plugin or configuration file

**Recovery:**

```bash
# Option A: Git restore (if committed)
git checkout HEAD -- path/to/deleted/file.py

# Option B: VM snapshot restore
# Via VMware UI: VM → Snapshot → Revert to Snapshot

# Option C: Git reflog (if deleted and committed)
git reflog
git checkout <commit-hash> -- path/to/file.py
```

**Recovery Time:** < 5 minutes

---

### Scenario 3: Complete System Failure

**Symptom:** VM won't boot, disk corruption, host machine failure

**Recovery:**

```bash
# Step 1: Create new Kali VM (or use backup VM)

# Step 2: Install Docker + Poetry + Git
sudo apt update
sudo apt install docker.io docker-compose-v2 git
curl -sSL https://install.python-poetry.org | python3 -

# Step 3: Clone repository
git clone https://github.com/crls-cyber/pentest-toolbox-v2.git
cd pentest-toolbox-v2

# Step 4: Restore .env from encrypted backup
gpg -d ~/encrypted_backup/.env.YYYYMMDD.gpg > deploy/.env

# Step 5: Start services
cd deploy
docker compose up -d
sleep 30

# Step 6: Restore database
cat ~/backups/postgres_YYYYMMDD.sql | \
  docker compose exec -T postgres psql -U pentest pentest_toolbox

# Step 7: Verify
curl http://localhost:5000/api/health
firefox http://localhost:5000
```

**Recovery Time:** ~1-2 hours

---

### Scenario 4: MinIO Data Loss

**Symptom:** Artifacts missing, MinIO container failure

**Recovery:**

```bash
# Stop services
docker compose down

# Remove corrupted MinIO volume
docker volume rm deploy_minio_data

# Restart MinIO
docker compose up -d minio
sleep 10

# Restore from backup
tar -xzf ~/Desktop/ToolBox_M1/backups/minio_YYYYMMDD.tar.gz -C /tmp

# Upload to MinIO
docker compose exec minio mc alias set local \
  http://localhost:9000 $MINIO_ROOT_USER $MINIO_ROOT_PASSWORD

docker compose exec minio mc mirror /tmp/minio_YYYYMMDD/artifacts \
  local/artifacts

# Restart all services
docker compose restart

# Verify
curl http://localhost:9000/minio/health/live
```

**Recovery Time:** ~30 minutes

---

## 📅 Backup Schedule

### Development Phase (J1-J10)

| Day | VM Snapshot | DB Dump | Config Backup | Git Push |
|-----|-------------|---------|---------------|----------|
| **J1** | ✅ Evening | ✅ Manual | ✅ After setup | ✅ Every commit |
| **J2-J3** | ✅ Evening | ⚠️ Optional | ❌ | ✅ Every commit |
| **J4** | ✅ Milestone | ✅ Manual | ✅ After changes | ✅ Every commit |
| **J5-J6** | ✅ Evening | ⚠️ Optional | ❌ | ✅ Every commit |
| **J7** | ✅ Milestone | ✅ Manual | ✅ After UI | ✅ Every commit |
| **J8-J9** | ✅ Evening | ⚠️ Optional | ❌ | ✅ Every commit |
| **J10** | ✅ **FINAL MVP** | ✅ Manual | ✅ Final | ✅ Every commit |

### Production Phase (Phase 2+)

| Frequency | VM Snapshot | DB Dump | MinIO | Config |
|-----------|-------------|---------|-------|--------|
| **Daily** | ❌ | ✅ Automated (cron) | ❌ | ❌ |
| **Weekly** | ✅ Sunday 2 AM | — | ✅ Automated | ❌ |
| **Monthly** | ✅ + Archive | — | ✅ + Archive | ✅ |
| **Before changes** | ✅ Manual | ❌ | ❌ | ✅ |

---

## 📍 Storage Locations

### Local Storage
```bash
~/Desktop/ToolBox_M1/backups/
├── postgres_YYYYMMDD.sql          # Database dumps
├── minio_YYYYMMDD.tar.gz          # Artifact archives
├── config/
│   ├── .env.YYYYMMDD.gpg          # Encrypted secrets
│   └── docker-compose.yml.YYYYMMDD
└── snapshots.txt                   # List of VMware snapshots
```

### VMware Snapshots
```bash
Location (Windows host example)
C:\Users<user>\Documents\Virtual Machines\Kali*.vmdk
C:\Users<user>\Documents\Virtual Machines\Kali*.vmsn
```

### External Storage (Recommended)

- 💾 **Encrypted USB key** (for `.env` backups)
- 💾 **External HDD** (for large VM snapshots)
- ☁️ **Private Git server** (optional, for code only)

**⚠️ DO NOT use:**
- ❌ Public cloud (Dropbox, Google Drive) for unencrypted backups
- ❌ Unencrypted USB keys
- ❌ Email attachments

---

## 🧪 Testing Backups

### Monthly Backup Test (Recommended)

**Purpose:** Verify backups are restorable

**Procedure:**

```bash
# Test 1: Database restore (dry run)
docker compose exec postgres psql -U pentest -d template1 \
  -c "CREATE DATABASE test_restore;"

cat ~/Desktop/ToolBox_M1/backups/postgres_latest.sql | \
  docker compose exec -T postgres psql -U pentest test_restore

# Verify
docker compose exec postgres psql -U pentest test_restore \
  -c "SELECT COUNT(*) FROM users;"

# Cleanup
docker compose exec postgres psql -U pentest -d template1 \
  -c "DROP DATABASE test_restore;"
```

**Expected:** Restore completes without errors

```bash
# Test 2: VM snapshot restore
# Via VMware UI: Revert to snapshot, verify services start

docker compose ps
# All services should be "Up"
```

**Expected:** System boots and all services start

---

## 📝 Backup Checklist

### Before Starting Development

- [ ] Create initial VM snapshot (`00_Base_Kali_Clean`)
- [ ] Backup `.env.example` to external USB
- [ ] Verify Git remote is accessible (`git remote -v`)

### Daily Development

- [ ] Git commit + push at end of day
- [ ] VM snapshot if major changes made
- [ ] Database dump if significant data added

### Before Major Changes

- [ ] VM snapshot with descriptive name
- [ ] Backup current `.env` file
- [ ] Test rollback procedure (optional)

### End of Project

- [ ] Final VM snapshot (`MVP_Final`)
- [ ] Final database dump
- [ ] Archive all backups to external drive
- [ ] Verify GitHub repository is up to date
- [ ] Export `.env` to encrypted archive

---

## 🔐 Security Recommendations

1. **Encrypt sensitive backups** (especially `.env`)
2. **Store `.env` backups offline** (encrypted USB)
3. **Use strong encryption** (GPG, VeraCrypt)
4. **Test recovery procedures** monthly
5. **Keep 3-2-1 rule** (3 copies, 2 media, 1 offsite)

---

**Version:** v1.0.0-mvp  
**Last Updated:** 14 mai 2026  
**Next Review:** Phase 2 (before production deployment)
