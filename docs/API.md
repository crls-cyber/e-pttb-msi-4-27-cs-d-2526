# 🔌 API Documentation — ToolBox Pentest M1

**Version :** v1.0.0-mvp  
**Base URL :** `http://localhost:5000`  
**Date :** 14 mai 2026

---

## 📋 Table des matières

- [Authentication](#authentication)
- [Jobs Management](#jobs-management)
- [Findings](#findings)
- [Reports](#reports)
- [Workflows](#workflows)
- [External Upload](#external-upload)
- [Users](#users)
- [Error Handling](#error-handling)

---

## 🔐 Authentication

### POST `/api/auth/login`

Authenticate user and create session.

**Request Body:**
```json
{
  "username": "admin",
  "password": "Test123!"
}
```

**Response (200 OK):**
```json
{
  "message": "Login successful",
  "user": {
    "id": "uuid",
    "username": "admin"
  }
}
```

**Response (401 Unauthorized):**
```json
{
  "error": "Invalid credentials"
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"Test123!"}' \
  -c cookies.txt
```

---

### POST `/api/auth/logout`

Logout user and destroy session.

**Response (200 OK):**
```json
{
  "message": "Logged out successfully"
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/api/auth/logout \
  -b cookies.txt
```

---

## 💼 Jobs Management

### POST `/api/jobs`

Create and launch a new scan job.

**Authentication:** Required (Cookie or Bearer token)

**Request Body:**
```json
{
  "plugin": "nmap",
  "config": {
    "target": "192.168.145.102",
    "ports": "80,443,22"
  }
}
```

**Plugin-specific configs:**

**Nmap:**
```json
{
  "plugin": "nmap",
  "config": {
    "target": "192.168.145.102",
    "ports": "1-1000",
    "scan_type": "-sV"
  }
}
```

**Nuclei:**
```json
{
  "plugin": "nuclei",
  "config": {
    "target": "http://192.168.145.102"
  }
}
```

**SQLmap:**
```json
{
  "plugin": "sqlmap",
  "config": {
    "target": "http://192.168.145.102/test.php?id=1",
    "level": 1,
    "risk": 1
  }
}
```

**theHarvester:**
```json
{
  "plugin": "theharvester",
  "config": {
    "domain": "example.com",
    "source": "crtsh",
    "limit": 100
  }
}
```

**Hydra:**
```json
{
  "plugin": "hydra",
  "config": {
    "target": "192.168.145.102",
    "service": "ftp",
    "username": "msfadmin",
    "password": "msfadmin",
    "threads": 4,
    "confirmed": true
  }
}
```

**Response (201 Created):**
```json
{
  "job_id": "uuid",
  "status": "pending",
  "task_id": "celery-task-uuid"
}
```

**Response (400 Bad Request):**
```json
{
  "error": "Plugin 'unknown' not found"
}
```

---

### GET `/api/jobs`

List all jobs for the authenticated user.

**Authentication:** Required

**Query Parameters:**
- `status` (optional): Filter by status (`pending`, `running`, `completed`, `failed`)
- `plugin` (optional): Filter by plugin name
- `limit` (optional): Number of results (default: 50)

**Response (200 OK):**
```json
{
  "jobs": [
    {
      "id": "uuid",
      "plugin_name": "nmap",
      "status": "completed",
      "created_at": "2026-05-14T10:30:00Z",
      "config": {
        "target": "192.168.145.102"
      }
    }
  ],
  "total": 25
}
```

**Example:**
```bash
curl http://localhost:5000/api/jobs?status=completed \
  -b cookies.txt
```

---

### GET `/api/jobs/{job_id}`

Get detailed job information with findings.

**Authentication:** Required

**Response (200 OK):**
```json
{
  "job": {
    "id": "uuid",
    "plugin_name": "nmap",
    "status": "completed",
    "created_at": "2026-05-14T10:30:00Z",
    "started_at": "2026-05-14T10:30:05Z",
    "completed_at": "2026-05-14T10:30:18Z",
    "config": {
      "target": "192.168.145.102"
    }
  },
  "findings": [
    {
      "id": "uuid",
      "title": "Open port 80/tcp on 192.168.145.102",
      "severity": "medium",
      "description": "Port 80/tcp is open running http (Apache httpd 2.2.8)...",
      "created_at": "2026-05-14T10:30:18Z"
    }
  ],
  "artifacts": [
    {
      "id": "uuid",
      "filename": "nmap_output.xml",
      "size_bytes": 5432,
      "download_url": "/api/artifacts/uuid"
    }
  ]
}
```

**Response (404 Not Found):**
```json
{
  "error": "Job not found"
}
```

---

### DELETE `/api/jobs/{job_id}`

Cancel a pending or running job.

**Authentication:** Required (Analyst or Admin role)

**Response (200 OK):**
```json
{
  "message": "Job cancelled successfully"
}
```

**Response (400 Bad Request):**
```json
{
  "error": "Cannot cancel completed job"
}
```

---

## 🔍 Findings

### GET `/api/findings`

List findings with filters.

**Authentication:** Required

**Query Parameters:**
- `job_id` (optional): Filter by job
- `severity` (optional): `critical`, `high`, `medium`, `low`, `info`
- `limit` (optional): Number of results (default: 100)

**Response (200 OK):**
```json
{
  "findings": [
    {
      "id": "uuid",
      "job_id": "uuid",
      "title": "Valid credentials found (1)",
      "severity": "critical",
      "description": "Hydra successfully brute-forced 1 credential(s)...",
      "cvss_score": null,
      "cve_id": null,
      "created_at": "2026-05-14T14:25:17Z"
    }
  ],
  "total": 150
}
```

---

### GET `/api/findings/{finding_id}`

Get detailed finding information.

**Authentication:** Required

**Response (200 OK):**
```json
{
  "finding": {
    "id": "uuid",
    "job_id": "uuid",
    "title": "PostgreSQL File Read - 192.168.145.102:5432",
    "severity": "high",
    "description": "Read and list the files within the PostgreSQL database...",
    "cvss_score": 7.5,
    "cve_id": "CVE-2019-9193",
    "remediation": "Update PostgreSQL to latest version...",
    "created_at": "2026-05-14T10:51:33Z"
  }
}
```

---

## 📄 Reports

### GET `/api/reports/{job_id}/html`

Generate HTML report for a job.

**Authentication:** Required

**Response (200 OK):**
```html
<!DOCTYPE html>
<html>
<!-- Full HTML report with findings, charts, etc. -->
</html>
```

---

### GET `/api/reports/{job_id}/pdf`

Generate PDF report for a job.

**Authentication:** Required

**Response (200 OK):**
- Content-Type: `application/pdf`
- Binary PDF file

**Example:**
```bash
curl http://localhost:5000/api/reports/{job_id}/pdf \
  -b cookies.txt \
  -o report.pdf
```

---

### GET `/api/reports/{job_id}/csv`

Export findings as CSV.

**Authentication:** Required

**Response (200 OK):**
- Content-Type: `text/csv`
- CSV file with headers: `Title,Severity,Description,CVE,CVSS,Date`

---

## 🔄 Workflows

### POST `/api/workflows/web-pentest`

Launch automated web pentest workflow (Nmap → Nuclei → SQLmap).

**Authentication:** Required (Analyst or Admin role)

**Request Body:**
```json
{
  "target": "192.168.145.102",
  "ports": "80,443"
}
```

**Response (200 OK):**
```json
{
  "message": "Web pentest workflow started (Nmap → Nuclei → SQLmap)",
  "status": "running",
  "target": "192.168.145.102",
  "workflow_id": "celery-chain-uuid"
}
```

**Workflow creates 3 jobs:**
1. Nmap scan (ports discovery)
2. Nuclei scan (CVE detection)
3. SQLmap scan (SQL injection)

Jobs are executed **sequentially** and can be monitored via `/api/jobs`.

---

## 📤 External Upload

### POST `/api/upload-external`

Upload external files (PCAP, Metasploit logs) for parsing.

**Authentication:** Required

**Request (multipart/form-data):**
- `file`: File to upload (.pcap, .pcapng, .cap, .log, .txt)
- `parser_type`: `auto`, `wireshark`, or `metasploit`

**Response (200 OK):**
```json
{
  "success": true,
  "job_id": "uuid",
  "findings_count": 3,
  "summary": "PCAP analysis: 1250 packets, 5 protocols, 3 findings",
  "message": "Wireshark file parsed successfully"
}
```

**Supported parsers:**
- **Wireshark** (.pcap, .pcapng, .cap, max 100MB): HTTP traffic, FTP credentials, protocol stats
- **Metasploit** (.log, .txt, max 50MB): Exploits, sessions, vulnerabilities

**Example:**
```bash
curl -X POST http://localhost:5000/api/upload-external \
  -b cookies.txt \
  -F "file=@capture.pcap" \
  -F "parser_type=auto"
```

---

## 👤 Users

### GET `/api/users/me`

Get current user profile.

**Authentication:** Required

**Response (200 OK):**
```json
{
  "user": {
    "id": "uuid",
    "username": "admin",
    "email": "admin@toolbox.local",
    "roles": ["admin"],
    "created_at": "2026-05-08T18:59:55Z"
  }
}
```

---

## ❌ Error Handling

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created |
| 400 | Bad Request | Invalid input |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 500 | Internal Server Error | Server error |

### Error Response Format

```json
{
  "error": "Descriptive error message",
  "details": {
    "field": "Specific field error (optional)"
  }
}
```

---

## 🔒 Security

### Authentication Methods

1. **Session Cookie** (recommended for web UI)
   - Set via `/api/auth/login`
   - Httponly, Secure (in production)

2. **Bearer Token** (for API clients)
```bash
   curl -H "Authorization: Bearer <token>" ...
```

### RBAC Roles

| Role | Permissions |
|------|-------------|
| **Admin** | All operations, user management |
| **Analyst** | Create/view jobs, generate reports |
| **Viewer** | View jobs and findings (read-only) |

### Rate Limiting

- **Authentication endpoints**: 5 attempts / 5 minutes
- **Job creation**: 10 jobs / minute
- **Report generation**: 5 reports / minute

---

## 📊 Pagination

List endpoints support pagination: GET /api/jobs?limit=20&offset=40

**Parameters:**
- `limit`: Results per page (default: 50, max: 100)
- `offset`: Skip N results

**Response includes:**
```json
{
  "data": [...],
  "total": 150,
  "limit": 20,
  "offset": 40
}
```

---

## 🧪 Testing

### Health Check

```bash
curl http://localhost:5000/api/health
```

**Response:**
```json
{
  "status": "healthy",
  "services": {
    "database": "ok",
    "redis": "ok",
    "celery": "ok"
  }
}
```

---

## 📝 Examples

### Full Workflow Example

```bash
# 1. Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"Test123!"}' \
  -c cookies.txt

# 2. Launch Nmap scan
JOB_ID=$(curl -X POST http://localhost:5000/api/jobs \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -d '{
    "plugin":"nmap",
    "config":{"target":"192.168.145.102","ports":"80,443"}
  }' | jq -r '.job_id')

# 3. Check status
curl http://localhost:5000/api/jobs/$JOB_ID -b cookies.txt

# 4. Get findings
curl http://localhost:5000/api/findings?job_id=$JOB_ID -b cookies.txt

# 5. Download PDF report
curl http://localhost:5000/api/reports/$JOB_ID/pdf \
  -b cookies.txt \
  -o report.pdf
```

---

**Version:** v1.0.0-mvp  
**Last Updated:** 14 mai 2026  
**Maintainer:** Carlos (Groupe M1 Cybersécurité)
