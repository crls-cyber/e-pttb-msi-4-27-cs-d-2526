# Future Improvements — Pentest ToolBox v2

**Last updated:** June 26, 2026

Planned features and improvements, by order of priority.

---

### I. ZAP — `_wait_for_spider()` timeout fix

**Priority:** 🔴 Critical — **30 minutes**

`_wait_for_spider()` has no timeout parameter, unlike `_wait_for_scan()` (600s).
The **Web App Audit** workflow can block indefinitely on certain targets.

**Workaround:** `docker compose restart worker` if blocked.
**Affected file:** `plugins/zap/plugin.py`

---

### II. Mission export & archiving

**Priority:** 🔴 High — **1 day**

On a physical Kali machine (no hypervisor, no VMware snapshots), an applicative
export is the only way to preserve mission results before wiping the machine:

- PostgreSQL dump (findings, jobs, audit logs)
- MinIO artifacts archive
- Global mission PDF report
- GPG-encrypted archive → delivered to client or stored internally
- Machine wipe procedure (LUKS)

---

### III. Fourth Pivot Chain — Full Attack Chain

**Priority:** 🟡 High — **1-2 days**

Chain all three existing Pivot Chains into a single action:

```
CIDR → Network Pivot Discovery
       → [per discovered host] Credential Access Discovery
                               → [per open service] Exploitation Readiness
```

---

### IV. Exploit library by port/protocol

**Priority:** 🟡 High — **3-5 days**

Extension of Pivot Chain #3 (Exploitation Readiness Report):
- Known exploits mapped by port (22→SSH, 21→FTP, 445→SMB...)
- CVE → precise Metasploit module mapping
- Automatic recommendations without human intervention

---

### V. Mission purge (admin UI)

**Priority:** 🟡 High — **1 day**

Admin button in Settings → single-action cleanup:
jobs, findings, targets, audit logs, MinIO artifacts — with double confirmation.

> **RGPD note:** This does not replace physical disk destruction (LUKS wipe)
> at end of engagement. See `docs/RGPD_POLICY.md`.

---

### VI. Docker volumes read-only (production mode)

**Priority:** 🟡 Medium — **30 minutes**

Mount `core/`, `ui/`, `plugins/` as `:ro` in production to prevent accidental
code modification during a live engagement.

---

### VII. Full French translation (i18n)

**Priority:** 🟡 Medium — **2-3 days**

The i18n infrastructure (`ui/i18n.py`) and EN/FR selector are already in place.
Remaining work: systematic translation of all UI strings.

---

### VIII. API documentation (Swagger/OpenAPI)

**Priority:** 🟢 Low — **1-2 days**

Auto-generated REST API documentation via Flask-RESTX or Flasgger.

---

### IX. Granular RBAC (permissions table)

**Priority:** 🟢 Low — **1 day**

The `permissions` table exists in the database but is unused. Implement fine-grained
permissions per plugin/workflow using the existing `@require_permission()` decorator.

---

### X. External integrations (VirusTotal, Shodan)

**Priority:** 🟢 Low — **2-3 days**

Optional, disabled by default (cloud dependency vs. local-only principle).
Requires API keys and controlled internet access.

---

### XI. Machine Learning — findings analysis plugin

**Priority:** 🟢 Low — **research + 5-10 days**

The modular plugin architecture supports adding an ML plugin without touching the core.
Use case: automatic prioritization of critical targets, CVE correlation, risk scoring.

---

### XII. Configurable workflows

**Priority:** 🟢 Low — **2-3 days**

Allow per-step parameter customization before workflow launch,
via collapsible `<details>` sections — consistent with dedicated plugin pages.

---

### XIII. theHarvester — timeout handling

**Priority:** 🟢 Low — **1 day**

Implement retry logic with fallback on alternative sources when rate-limited
by external search engines (Google, Bing, Yahoo).

---

*See also: `docs/STORAGE_GOVERNANCE.md` and `docs/RGPD_POLICY.md`*
