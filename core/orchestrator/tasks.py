"""Celery tasks."""
from .celery_app import celery_app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.models import Job, Finding
from core.plugins import executor
import os
from dotenv import load_dotenv
import uuid
from datetime import datetime

load_dotenv()

# Database connection
POSTGRES_USER = os.getenv('POSTGRES_USER', 'pentest')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'password')
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
POSTGRES_DB = os.getenv('POSTGRES_DB', 'pentest_toolbox')

DATABASE_URL = f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}'


@celery_app.task(bind=True, name='core.orchestrator.tasks.run_plugin')
def run_plugin(self, job_id, plugin_name, config):
    """Execute a plugin scan."""
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Get job from database
        job = session.query(Job).filter_by(id=job_id).first()
        if not job:
            return {'error': 'Job not found'}
        
        # Update job status to running
        job.status = 'running'
        job.started_at = datetime.utcnow()
        session.commit()
        session.refresh(job)  # Force refresh from DB
        
        # Execute plugin via executor
        result = executor.execute(plugin_name, config)
        
        if result['success']:
            # Create findings in database
            for finding_data in result['findings']:
                finding = Finding(
                    id=uuid.uuid4(),
                    job_id=job.id,
                    title=finding_data['title'],
                    severity=finding_data['severity'],
                    description=finding_data.get('description', ''),
                    remediation=finding_data.get('remediation', ''),
                    cvss_score=finding_data.get('cvss_score'),
                    cve_id=finding_data.get('cve_id')
                )
                session.add(finding)
            
            # Update job status to completed
            job.status = 'completed'
            job.completed_at = datetime.utcnow()
            session.commit()
            
            return {
                'job_id': str(job_id),
                'plugin': plugin_name,
                'status': 'completed',
                'findings_count': len(result['findings']),
                'duration': result['duration']
            }
        else:
            # Plugin execution failed
            job.status = 'failed'
            job.completed_at = datetime.utcnow()
            job.error = result['error']
            session.commit()
            
            return {
                'job_id': str(job_id),
                'plugin': plugin_name,
                'status': 'failed',
                'error': result['error']
            }
        
    except Exception as e:
        # Update job status to failed
        if job:
            job.status = 'failed'
            job.error = str(e)
            session.commit()
        
        return {'error': str(e)}
        
    finally:
        session.close()


@celery_app.task(name='core.orchestrator.tasks.hello_world')
def hello_world():
    """Test task."""
    return 'Hello from Celery!'


# ── Pivot Chains — Network Pivot Discovery ──────────────────────────────────
import re


@celery_app.task(bind=True, name='core.orchestrator.tasks.pivot_discovery_orchestrator')
def pivot_discovery_orchestrator(self, parent_job_id, cidr, user_id):
    """
    Data-driven pivot discovery: scan a CIDR range with Nmap, then dynamically
    launch Nuclei + WhatWeb on every host actually discovered as active.

    Unlike the static workflows in core/orchestrator/workflows.py (which create
    all jobs upfront with a fixed target), this orchestrator creates follow-up
    jobs AFTER reading the Nmap results — true findings-driven chaining.

    Args:
        parent_job_id: ID of the pre-created Nmap Job (status='pending')
        cidr: CIDR range to scan (e.g. "192.168.145.0/24")
        user_id: UUID of the user who launched this chain

    Returns:
        dict summary: hosts found, jobs created
    """
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Step 1 — run Nmap synchronously (reuse the same execution path as run_plugin)
        job = session.query(Job).filter_by(id=parent_job_id).first()
        if not job:
            return {'error': 'Parent Nmap job not found'}

        job.status = 'running'
        job.started_at = datetime.utcnow()
        session.commit()

        nmap_config = {'target': cidr, 'scan_type': '-sV'}
        result = executor.execute('nmap', nmap_config)

        if not result['success']:
            job.status = 'failed'
            job.completed_at = datetime.utcnow()
            job.error = result['error']
            session.commit()
            return {'error': f"Nmap scan failed: {result['error']}"}

        # Save Nmap findings
        for finding_data in result['findings']:
            finding = Finding(
                id=uuid.uuid4(),
                job_id=job.id,
                title=finding_data['title'],
                severity=finding_data['severity'],
                description=finding_data.get('description', ''),
                remediation=finding_data.get('remediation', ''),
                cvss_score=finding_data.get('cvss_score'),
                cve_id=finding_data.get('cve_id')
            )
            session.add(finding)

        job.status = 'completed'
        job.completed_at = datetime.utcnow()
        session.commit()

        # Step 2 — extract unique active host IPs from Nmap finding titles
        # Title format: "Open port {port}/{proto} on {ip} (hostname)"
        host_ips = set()
        for finding_data in result['findings']:
            match = re.search(r'on (\d+\.\d+\.\d+\.\d+)', finding_data['title'])
            if match:
                host_ips.add(match.group(1))

        if not host_ips:
            return {
                'nmap_job_id': str(job.id),
                'hosts_found': 0,
                'message': 'No active hosts discovered on this range — no follow-up jobs created.',
                'follow_up_jobs': []
            }

        # Step 3 — dynamically create + launch Nuclei and WhatWeb for each host
        follow_up_jobs = []
        for ip in sorted(host_ips):
            nuclei_job = Job(
                id=uuid.uuid4(),
                user_id=user_id,
                plugin_name='nuclei',
                config={'target': f'http://{ip}'},
                status='pending'
            )
            whatweb_job = Job(
                id=uuid.uuid4(),
                user_id=user_id,
                plugin_name='whatweb',
                config={'target': f'http://{ip}', 'aggression': 1},
                status='pending'
            )
            session.add(nuclei_job)
            session.add(whatweb_job)
            session.commit()

            run_plugin.delay(str(nuclei_job.id), 'nuclei', nuclei_job.config)
            run_plugin.delay(str(whatweb_job.id), 'whatweb', whatweb_job.config)

            follow_up_jobs.append({
                'host': ip,
                'nuclei_job_id': str(nuclei_job.id),
                'whatweb_job_id': str(whatweb_job.id)
            })

        return {
            'nmap_job_id': str(job.id),
            'hosts_found': len(host_ips),
            'hosts': sorted(host_ips),
            'follow_up_jobs': follow_up_jobs,
            'message': f'Discovered {len(host_ips)} active host(s) — launched Nuclei + WhatWeb on each.'
        }

    except Exception as e:
        if job:
            job.status = 'failed'
            job.error = str(e)
            session.commit()
        return {'error': str(e)}
    finally:
        session.close()

# ── Pivot Chains — Credential Access Discovery ──────────────────────────────

# Port → Hydra service name mapping for auto-detected authentication services
HYDRA_PORT_SERVICE_MAP = {
    21: 'ftp',
    22: 'ssh',
    23: 'telnet',
    445: 'smb',
    1433: 'mssql',
    3306: 'mysql',
    3389: 'rdp',
    5432: 'postgres',
}

HYDRA_DEFAULT_PASSLIST = ['password', 'admin', '123456', 'root', 'toor', 'test']
HYDRA_DEFAULT_USERLIST = ['admin', 'root', 'user', 'test', 'administrator']


@celery_app.task(bind=True, name='core.orchestrator.tasks.pivot_credential_access')
def pivot_credential_access(self, parent_job_id, cidr, user_id):
    """
    Data-driven credential access discovery: scan a CIDR range with Nmap,
    then dynamically launch Hydra ONLY on (host, service) pairs where an
    authentication service was actually found open — no blind brute-force
    on ports that aren't even listening.

    Args:
        parent_job_id: ID of the pre-created Nmap Job (status='pending')
        cidr: CIDR range to scan (e.g. "192.168.145.0/24")
        user_id: UUID of the user who launched this chain

    Returns:
        dict summary: hosts found, auth services found, jobs created
    """
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Step 1 — run Nmap synchronously on the range, targeting common auth ports
        job = session.query(Job).filter_by(id=parent_job_id).first()
        if not job:
            return {'error': 'Parent Nmap job not found'}

        job.status = 'running'
        job.started_at = datetime.utcnow()
        session.commit()

        auth_ports = ','.join(str(p) for p in HYDRA_PORT_SERVICE_MAP.keys())
        nmap_config = {'target': cidr, 'ports': auth_ports, 'scan_type': '-sV'}
        result = executor.execute('nmap', nmap_config)

        if not result['success']:
            job.status = 'failed'
            job.completed_at = datetime.utcnow()
            job.error = result['error']
            session.commit()
            return {'error': f"Nmap scan failed: {result['error']}"}

        for finding_data in result['findings']:
            finding = Finding(
                id=uuid.uuid4(),
                job_id=job.id,
                title=finding_data['title'],
                severity=finding_data['severity'],
                description=finding_data.get('description', ''),
                remediation=finding_data.get('remediation', ''),
                cvss_score=finding_data.get('cvss_score'),
                cve_id=finding_data.get('cve_id')
            )
            session.add(finding)

        job.status = 'completed'
        job.completed_at = datetime.utcnow()
        session.commit()

        # Step 2 — parse findings to extract (host, port) pairs for auth services
        # Title format: "Open port {port}/{proto} on {ip} (hostname)"
        auth_targets = []  # list of (ip, port, hydra_service)
        seen = set()
        for finding_data in result['findings']:
            title = finding_data['title']
            match = re.search(r'Open port (\d+)/\w+ on (\d+\.\d+\.\d+\.\d+)', title)
            if not match:
                continue
            port = int(match.group(1))
            ip = match.group(2)
            hydra_service = HYDRA_PORT_SERVICE_MAP.get(port)
            if hydra_service and (ip, port) not in seen:
                seen.add((ip, port))
                auth_targets.append((ip, port, hydra_service))

        if not auth_targets:
            return {
                'nmap_job_id': str(job.id),
                'auth_services_found': 0,
                'message': 'No authentication services discovered on this range — no Hydra jobs created.',
                'follow_up_jobs': []
            }

        # Step 3 — dynamically create + launch Hydra for each (host, service) pair
        follow_up_jobs = []
        for ip, port, hydra_service in auth_targets:
            hydra_job = Job(
                id=uuid.uuid4(),
                user_id=user_id,
                plugin_name='hydra',
                config={
                    'target': ip,
                    'service': hydra_service,
                    'port': port,
                    'passlist': list(HYDRA_DEFAULT_PASSLIST),
                    'userlist': list(HYDRA_DEFAULT_USERLIST),
                },
                status='pending'
            )
            session.add(hydra_job)
            session.commit()

            run_plugin.delay(str(hydra_job.id), 'hydra', hydra_job.config)

            follow_up_jobs.append({
                'host': ip,
                'port': port,
                'service': hydra_service,
                'hydra_job_id': str(hydra_job.id)
            })

        return {
            'nmap_job_id': str(job.id),
            'auth_services_found': len(auth_targets),
            'targets': [{'host': t[0], 'port': t[1], 'service': t[2]} for t in auth_targets],
            'follow_up_jobs': follow_up_jobs,
            'message': f'Discovered {len(auth_targets)} authentication service(s) — launched Hydra on each.'
        }

    except Exception as e:
        if job:
            job.status = 'failed'
            job.error = str(e)
            session.commit()
        return {'error': str(e)}
    finally:
        session.close()

# ── Pivot Chains — Exploitation Readiness Report ────────────────────────────

# Known service-version → Metasploit module mapping (curated, kept short on purpose).
# Matched against Nmap "Open port X/tcp on IP (service version)" findings.
KNOWN_EXPLOIT_MODULES = [
    {
        'match': re.compile(r'vsftpd[\s/]?2\.3\.4', re.IGNORECASE),
        'service': 'vsftpd 2.3.4',
        'module': 'exploit/unix/ftp/vsftpd_234_backdoor',
        'note': 'Known backdoor — opens a root shell on port 6200 when triggered.'
    },
    {
        'match': re.compile(r'unrealircd[\s/]?3\.2\.8\.1', re.IGNORECASE),
        'service': 'UnrealIRCd 3.2.8.1',
        'module': 'exploit/unix/irc/unreal_ircd_3281_backdoor',
        'note': 'Known backdoor in the Debian-patched source archive.'
    },
    {
        'match': re.compile(r'distccd', re.IGNORECASE),
        'service': 'distccd',
        'module': 'exploit/unix/misc/distcc_exec',
        'note': 'Remote command execution via distcc daemon misconfiguration.'
    },
    {
        'match': re.compile(r'samba\s*3\.0\.2[0-2]', re.IGNORECASE),
        'service': 'Samba 3.0.20-3.0.22',
        'module': 'exploit/multi/samba/usermap_script',
        'note': 'Username map script command injection.'
    },
    {
        'match': re.compile(r'ingreslock', re.IGNORECASE),
        'service': 'ingreslock backdoor',
        'module': 'exploit/multi/misc/ingreslock_backdoor',
        'note': 'Backdoor listening on port 1524, drops directly to a root shell.'
    },
]


@celery_app.task(bind=True, name='core.orchestrator.tasks.pivot_exploitation_readiness')
def pivot_exploitation_readiness(self, parent_job_id, cidr, user_id):
    """
    Data-driven exploitation readiness report (Pivot Chains, no auto-exploit).

    Reuses Nmap + Nuclei scan results across the CIDR range to produce a
    prioritized, actionable summary for MANUAL follow-up with Metasploit,
    Burp Suite, or Wireshark (all upload-based tools in this toolbox — not
    automatable, so this chain prepares the ground instead of launching them).

    For every finding:
    - HIGH/CRITICAL findings with a CVE get a generic recommendation
      ("search cve:XXXX-YYYYY in msfconsole").
    - Known service/version combos (curated short list) get a precise
      Metasploit module recommendation when available.

    Args:
        cidr: CIDR range to scan (e.g. "192.168.145.0/24")
        user_id: UUID of the user who launched this chain

    Returns:
        dict: prioritized findings with recommendations (no new jobs created
        beyond the Nmap+Nuclei scans needed to gather the data).
    """
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Step 1 — run Nmap on the pre-created job (reuse the job created by the API endpoint)
        nmap_job = session.query(Job).filter_by(id=parent_job_id).first()
        if not nmap_job:
            return {'error': 'Parent Nmap job not found'}

        nmap_job.status = 'running'
        nmap_job.started_at = datetime.utcnow()
        session.commit()

        nmap_result = executor.execute('nmap', {'target': cidr, 'scan_type': '-sV'})
        if not nmap_result['success']:
            nmap_job.status = 'failed'
            nmap_job.error = nmap_result['error']
            session.commit()
            return {'error': f"Nmap scan failed: {nmap_result['error']}"}

        for finding_data in nmap_result['findings']:
            session.add(Finding(
                id=uuid.uuid4(), job_id=nmap_job.id,
                title=finding_data['title'], severity=finding_data['severity'],
                description=finding_data.get('description', ''),
                remediation=finding_data.get('remediation', ''),
                cvss_score=finding_data.get('cvss_score'), cve_id=finding_data.get('cve_id')
            ))
        nmap_job.status = 'completed'
        nmap_job.completed_at = datetime.utcnow()
        session.commit()

        # Step 2 — extract unique active hosts
        host_ips = set()
        for f in nmap_result['findings']:
            m = re.search(r'on (\d+\.\d+\.\d+\.\d+)', f['title'])
            if m:
                host_ips.add(m.group(1))

        if not host_ips:
            return {
                'nmap_job_id': str(nmap_job.id),
                'hosts_found': 0,
                'message': 'No active hosts discovered — no readiness report to generate.',
                'high_value_targets': []
            }

        # Step 3 — Nuclei scan on each discovered host (vuln/CVE detection)
        nuclei_jobs_summary = []
        all_nuclei_findings = []
        for ip in sorted(host_ips):
            nuclei_job = Job(
                id=uuid.uuid4(), user_id=user_id, plugin_name='nuclei',
                config={'target': f'http://{ip}'}, status='running'
            )
            session.add(nuclei_job)
            session.commit()

            nuclei_result = executor.execute('nuclei', {'target': f'http://{ip}'})
            if nuclei_result['success']:
                for fd in nuclei_result['findings']:
                    session.add(Finding(
                        id=uuid.uuid4(), job_id=nuclei_job.id,
                        title=fd['title'], severity=fd['severity'],
                        description=fd.get('description', ''),
                        remediation=fd.get('remediation', ''),
                        cvss_score=fd.get('cvss_score'), cve_id=fd.get('cve_id')
                    ))
                    fd['_host'] = ip
                    all_nuclei_findings.append(fd)
                nuclei_job.status = 'completed'
            else:
                nuclei_job.status = 'failed'
                nuclei_job.error = nuclei_result.get('error', 'Unknown error')
            nuclei_job.completed_at = datetime.utcnow()
            session.commit()
            nuclei_jobs_summary.append({'host': ip, 'nuclei_job_id': str(nuclei_job.id), 'status': nuclei_job.status})

        # Step 4 — build prioritized exploitation readiness report
        cve_pattern = re.compile(r'cve-\d{4}-\d+', re.IGNORECASE)
        high_value = []

        # 4a. Precise recommendations from known Nmap service/version matches
        for f in nmap_result['findings']:
            for known in KNOWN_EXPLOIT_MODULES:
                if known['match'].search(f.get('description', '') + ' ' + f.get('title', '')):
                    host_match = re.search(r'on (\d+\.\d+\.\d+\.\d+)', f['title'])
                    high_value.append({
                        'host': host_match.group(1) if host_match else 'unknown',
                        'finding': f['title'],
                        'severity': 'critical',
                        'recommendation_type': 'precise',
                        'recommendation': f"Metasploit module: {known['module']}",
                        'note': known['note'],
                        'tool': 'metasploit'
                    })

        # 4b. Generic CVE-based recommendations from Nuclei HIGH/CRITICAL findings
        for f in all_nuclei_findings:
            if f.get('severity') not in ('high', 'critical'):
                continue
            cve_match = cve_pattern.search(f.get('description', '') + ' ' + f.get('title', ''))
            cve_id = cve_match.group(0).upper() if cve_match else None
            high_value.append({
                'host': f.get('_host', 'unknown'),
                'finding': f['title'],
                'severity': f['severity'],
                'recommendation_type': 'generic',
                'recommendation': (
                    f"search cve:{cve_id.replace('CVE-', '')} in msfconsole" if cve_id
                    else "Review manually — no CVE auto-extracted; check Nuclei template reference."
                ),
                'note': f"Detected by Nuclei. Consider manual verification with Burp Suite if web-facing.",
                'tool': 'metasploit_or_burp'
            })

        # Sort: precise recommendations first, then by severity
        severity_rank = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'info': 4}
        high_value.sort(key=lambda x: (
            0 if x['recommendation_type'] == 'precise' else 1,
            severity_rank.get(x['severity'], 9)
        ))


        # Step 5 — persist the report as Findings on the Nmap job, so it is
        # consultable from job_detail.html / Reports like any other scan,
        # since this task runs async via Celery (no direct HTTP response).
        for item in high_value:
            recommendation_severity = 'critical' if item['recommendation_type'] == 'precise' else item['severity']
            session.add(Finding(
                id=uuid.uuid4(),
                job_id=nmap_job.id,
                title=f"[Readiness] {item['finding']} ({item['host']})",
                severity=recommendation_severity,
                description=(
                    f"Recommendation type: {item['recommendation_type'].upper()}\n"
                    f"Tool: {item['tool']}\n"
                    f"Action: {item['recommendation']}\n"
                    f"Note: {item['note']}"
                ),
                remediation="See description for the recommended manual follow-up action."
            ))
        session.commit()

        return {
            'nmap_job_id': str(nmap_job.id),
            'hosts_found': len(host_ips),
            'hosts': sorted(host_ips),
            'nuclei_jobs': nuclei_jobs_summary,
            'high_value_targets': high_value,
            'message': (
                f"Readiness report: {len(host_ips)} host(s) scanned, "
                f"{len(high_value)} actionable item(s) found for manual follow-up "
                f"(Metasploit / Burp Suite / Wireshark)."
            )
        }

    except Exception as e:
        return {'error': str(e)}
    finally:
        session.close()
