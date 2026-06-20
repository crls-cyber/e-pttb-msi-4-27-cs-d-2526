"""Workflows orchestration."""
import uuid
import logging
from celery import chain
from core.orchestrator.tasks import run_plugin
from core.models.job import Job
from core.api.app import db

logger = logging.getLogger(__name__)


def web_pentest_workflow(target, user_id):
    """
    Basic web pentest workflow: Nmap → Nuclei → SQLmap

    Args:
        target: IP or domain (e.g., "192.168.145.102")
        user_id: UUID of the user running the workflow

    Returns:
        Celery AsyncResult
    """
    nmap_job = Job(
        id=str(uuid.uuid4()),
        user_id=user_id,
        plugin_name='nmap',
        config={'target': target, 'ports': '80,443,8080,8443'},
        status='pending'
    )
    nuclei_job = Job(
        id=str(uuid.uuid4()),
        user_id=user_id,
        plugin_name='nuclei',
        config={'target': f'http://{target}'},
        status='pending'
    )
    sqlmap_job = Job(
        id=str(uuid.uuid4()),
        user_id=user_id,
        plugin_name='sqlmap',
        config={
            'target': f'http://{target}/test_sqli.php?id=1',
            'level': 1,
            'risk': 1
        },
        status='pending'
    )

    db.session.add(nmap_job)
    db.session.add(nuclei_job)
    db.session.add(sqlmap_job)
    db.session.commit()

    nmap_task    = run_plugin.si(nmap_job.id,    'nmap',    nmap_job.config)
    nuclei_task  = run_plugin.si(nuclei_job.id,  'nuclei',  nuclei_job.config)
    sqlmap_task  = run_plugin.si(sqlmap_job.id,  'sqlmap',  sqlmap_job.config)

    workflow = chain(nmap_task, nuclei_task, sqlmap_task)
    return workflow.apply_async()


def recon_to_exploit_workflow(target, user_id, service='ssh', username=None):
    """
    Advanced pentest workflow: Nmap → Nuclei → Hydra

    Workflow logic:
    1. Nmap: Port scan + service detection on common vulnerable ports
    2. Nuclei: Vulnerability detection on discovered services
    3. Hydra: Credential brute-force on specified service

    Args:
        target: IP address (e.g., "192.168.200.133")
        user_id: UUID of the user running the workflow
        service: Service to brute-force (ssh, ftp, telnet, mysql) — default: ssh
        username: Optional username hint — default: common usernames list

    Returns:
        dict with job_ids for tracking
    """
    # Step 1: Nmap — common vulnerable ports
    nmap_job = Job(
        id=str(uuid.uuid4()),
        user_id=user_id,
        plugin_name='nmap',
        config={
            'target': target,
            'ports': '21,22,23,25,80,139,445,3306,5432,8080,8180'
        },
        status='pending'
    )

    # Step 2: Nuclei — vulnerability scan
    nuclei_job = Job(
        id=str(uuid.uuid4()),
        user_id=user_id,
        plugin_name='nuclei',
        config={'target': f'http://{target}'},
        status='pending'
    )

    # Step 3: Hydra — credential brute-force
    hydra_config = {
        'target': target,
        'service': service,
        'passlist': ['password', 'admin', '123456', 'root', 'toor', 'test']
    }
    if username:
        hydra_config['username'] = username
    else:
        # Hydra requires either username or userlist — fall back to a generic
        # common-usernames list when none is provided (no lab-specific default).
        hydra_config['userlist'] = ['admin', 'root', 'user', 'test', 'administrator']

    hydra_job = Job(
        id=str(uuid.uuid4()),
        user_id=user_id,
        plugin_name='hydra',
        config=hydra_config,
        status='pending'
    )

    db.session.add(nmap_job)
    db.session.add(nuclei_job)
    db.session.add(hydra_job)
    db.session.commit()

    logger.info(f"Recon-to-exploit workflow: Nmap ({nmap_job.id}) → Nuclei ({nuclei_job.id}) → Hydra ({hydra_job.id})")

    nmap_task   = run_plugin.si(nmap_job.id,   'nmap',   nmap_job.config)
    nuclei_task = run_plugin.si(nuclei_job.id, 'nuclei', nuclei_job.config)
    hydra_task  = run_plugin.si(hydra_job.id,  'hydra',  hydra_job.config)

    workflow = chain(nmap_task, nuclei_task, hydra_task)
    result = workflow.apply_async()

    return {
        'workflow_id': str(result.id),
        'nmap_job_id': nmap_job.id,
        'nuclei_job_id': nuclei_job.id,
        'hydra_job_id': hydra_job.id,
        'status': 'running'
    }


def web_pentest_advanced(target, user_id, sqli_url=None):
    """
    Advanced web pentest: Nmap → Nuclei → SQLmap

    Args:
        target: IP or domain (e.g., "192.168.200.133")
        user_id: UUID of the user
        sqli_url: Optional specific URL for SQLmap

    Returns:
        dict with job_ids
    """
    nmap_job = Job(
        id=str(uuid.uuid4()),
        user_id=user_id,
        plugin_name='nmap',
        config={
            'target': target,
            'ports': '80,443,8080,8443,8180'
        },
        status='pending'
    )
    nuclei_job = Job(
        id=str(uuid.uuid4()),
        user_id=user_id,
        plugin_name='nuclei',
        config={'target': f'http://{target}'},
        status='pending'
    )
    # No lab-specific default — use sqli_url if provided, else a generic guess based on target
    sqlmap_target = sqli_url or f'http://{target}/?id=1'
    sqlmap_job = Job(
        id=str(uuid.uuid4()),
        user_id=user_id,
        plugin_name='sqlmap',
        config={
            'target': sqlmap_target,
            'mode': 'detect',
            'level': 1,
            'risk': 1
        },
        status='pending'
    )

    db.session.add(nmap_job)
    db.session.add(nuclei_job)
    db.session.add(sqlmap_job)
    db.session.commit()

    logger.info(f"Web pentest workflow: Nmap ({nmap_job.id}) → Nuclei ({nuclei_job.id}) → SQLmap ({sqlmap_job.id})")

    nmap_task   = run_plugin.si(nmap_job.id,   'nmap',   nmap_job.config)
    nuclei_task = run_plugin.si(nuclei_job.id, 'nuclei', nuclei_job.config)
    sqlmap_task = run_plugin.si(sqlmap_job.id, 'sqlmap', sqlmap_job.config)

    workflow = chain(nmap_task, nuclei_task, sqlmap_task)
    result = workflow.apply_async()

    return {
        'workflow_id': str(result.id),
        'nmap_job_id': nmap_job.id,
        'nuclei_job_id': nuclei_job.id,
        'sqlmap_job_id': sqlmap_job.id,
        'status': 'running'
    }


def network_bruteforce(target, user_id, service='ssh', username='admin', password_list=None):
    """
    Network pentest: Nmap → Hydra

    Args:
        target: IP address
        user_id: UUID of the user
        service: Service to brute-force (ssh, ftp, etc.)
        username: Username to test
        password_list: List of passwords (default: common passwords)

    Returns:
        dict with job_ids
    """
    if password_list is None:
        password_list = ['password', 'admin', '123456', 'root', 'toor', 'test']

    nmap_job = Job(
        id=str(uuid.uuid4()),
        user_id=user_id,
        plugin_name='nmap',
        config={
            'target': target,
            'ports': '21,22,23,25,139,445,3389'
        },
        status='pending'
    )
    hydra_job = Job(
        id=str(uuid.uuid4()),
        user_id=user_id,
        plugin_name='hydra',
        config={
            'target': target,
            'service': service,
            'username': username,
            'passlist': password_list
        },
        status='pending'
    )

    db.session.add(nmap_job)
    db.session.add(hydra_job)
    db.session.commit()

    logger.info(f"Network bruteforce workflow: Nmap ({nmap_job.id}) → Hydra ({hydra_job.id})")

    nmap_task  = run_plugin.si(nmap_job.id,  'nmap',  nmap_job.config)
    hydra_task = run_plugin.si(hydra_job.id, 'hydra', hydra_job.config)

    workflow = chain(nmap_task, hydra_task)
    result = workflow.apply_async()

    return {
        'workflow_id': str(result.id),
        'nmap_job_id': nmap_job.id,
        'hydra_job_id': hydra_job.id,
        'status': 'running'
    }


def osint_recon(domain, user_id):
    """
    OSINT reconnaissance: theHarvester → subfinder

    Args:
        domain: Target domain (e.g., "example.com")
        user_id: UUID of the user

    Returns:
        dict with job_ids
    """
    harvester_job = Job(
        id=str(uuid.uuid4()),
        user_id=user_id,
        plugin_name='theharvester',
        config={
            'domain': domain,
            'sources': 'google,bing,yahoo'
        },
        status='pending'
    )
    subfinder_job = Job(
        id=str(uuid.uuid4()),
        user_id=user_id,
        plugin_name='subfinder',
        config={'domain': domain},
        status='pending'
    )

    db.session.add(harvester_job)
    db.session.add(subfinder_job)
    db.session.commit()

    logger.info(f"OSINT workflow: theHarvester ({harvester_job.id}) → subfinder ({subfinder_job.id})")

    harvester_task = run_plugin.si(harvester_job.id, 'theharvester', harvester_job.config)
    subfinder_task = run_plugin.si(subfinder_job.id, 'subfinder',    subfinder_job.config)

    workflow = chain(harvester_task, subfinder_task)
    result = workflow.apply_async()

    return {
        'workflow_id': str(result.id),
        'harvester_job_id': harvester_job.id,
        'subfinder_job_id': subfinder_job.id,
        'status': 'running'
    }


def quick_vuln_scan(target, user_id):
    """
    Quick vulnerability scan: Nmap → Nuclei

    Workflow logic:
    1. Nmap: Fast port scan on common ports
    2. Nuclei: Vulnerability detection on discovered services

    Args:
        target: IP or domain
        user_id: UUID of the user

    Returns:
        dict with job_ids
    """
    nmap_job = Job(
        id=str(uuid.uuid4()),
        user_id=user_id,
        plugin_name='nmap',
        config={
            'target': target,
            'ports': '80,443,22,21,23,8080,8443',
            'scan_type': '-sV'
        },
        status='pending'
    )
    nuclei_job = Job(
        id=str(uuid.uuid4()),
        user_id=user_id,
        plugin_name='nuclei',
        config={
            'target': f'http://{target}',
            'severity': 'critical,high,medium'
        },
        status='pending'
    )

    db.session.add(nmap_job)
    db.session.add(nuclei_job)
    db.session.commit()

    logger.info(f"Quick vuln scan: Nmap ({nmap_job.id}) → Nuclei ({nuclei_job.id})")

    nmap_task   = run_plugin.si(nmap_job.id,   'nmap',   nmap_job.config)
    nuclei_task = run_plugin.si(nuclei_job.id, 'nuclei', nuclei_job.config)

    workflow = chain(nmap_task, nuclei_task)
    result = workflow.apply_async()

    return {
        'workflow_id': str(result.id),
        'nmap_job_id': nmap_job.id,
        'nuclei_job_id': nuclei_job.id,
        'status': 'running'
    }


def _looks_like_ip(value):
    """Return True if value is a valid IPv4/IPv6 address."""
    import ipaddress
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


def full_external_recon(domain, user_id):
    """
    Full external reconnaissance: Subfinder → theHarvester → Nmap → WhatWeb

    Workflow logic:
    1. Subfinder: Subdomain enumeration
    2. theHarvester: OSINT (emails, hosts, IPs)
    3. Nmap: Port scan on discovered hosts
    4. WhatWeb: Web technology fingerprinting

    IMPORTANT: this workflow requires a real DNS domain (e.g. "example.com"),
    NOT an IP address. Subfinder/theHarvester operate on domain names only.
    For IP-only lab targets, use the "Quick Vuln Scan" workflow instead.
    See FUTURE_IMPROVEMENTS.md — "Workflow target-type validation" for the
    rationale behind this strict separation (deliberate design choice, not
    a limitation to "fix" by making this workflow IP-tolerant).

    Args:
        domain: Target domain (e.g., "example.com") — must NOT be an IP address
        user_id: UUID of the user

    Returns:
        dict with job_ids

    Raises:
        ValueError: if domain is an IP address
    """
    if _looks_like_ip(domain):
        raise ValueError(
            f"'{domain}' is an IP address — Full External Recon requires a domain name "
            f"(Subfinder/theHarvester need DNS). Use 'Quick Vuln Scan' for IP targets instead."
        )

    subfinder_job = Job(
        id=str(uuid.uuid4()),
        user_id=user_id,
        plugin_name='subfinder',
        config={'domain': domain},
        status='pending'
    )
    harvester_job = Job(
        id=str(uuid.uuid4()),
        user_id=user_id,
        plugin_name='theharvester',
        config={
            'domain': domain,
            'sources': 'google,bing,yahoo'
        },
        status='pending'
    )
    nmap_job = Job(
        id=str(uuid.uuid4()),
        user_id=user_id,
        plugin_name='nmap',
        config={
            'target': domain,
            'ports': '80,443,22,21,8080,8443',
            'scan_type': '-sV'
        },
        status='pending'
    )
    whatweb_job = Job(
        id=str(uuid.uuid4()),
        user_id=user_id,
        plugin_name='whatweb',
        config={
            'target': f'http://{domain}',
            'aggression': 1
        },
        status='pending'
    )

    db.session.add(subfinder_job)
    db.session.add(harvester_job)
    db.session.add(nmap_job)
    db.session.add(whatweb_job)
    db.session.commit()

    logger.info(f"Full external recon: Subfinder ({subfinder_job.id}) → theHarvester ({harvester_job.id}) → Nmap ({nmap_job.id}) → WhatWeb ({whatweb_job.id})")

    subfinder_task = run_plugin.si(subfinder_job.id, 'subfinder',    subfinder_job.config)
    harvester_task = run_plugin.si(harvester_job.id, 'theharvester', harvester_job.config)
    nmap_task      = run_plugin.si(nmap_job.id,      'nmap',         nmap_job.config)
    whatweb_task   = run_plugin.si(whatweb_job.id,   'whatweb',      whatweb_job.config)

    workflow = chain(subfinder_task, harvester_task, nmap_task, whatweb_task)
    result = workflow.apply_async()

    return {
        'workflow_id': str(result.id),
        'subfinder_job_id': subfinder_job.id,
        'harvester_job_id': harvester_job.id,
        'nmap_job_id': nmap_job.id,
        'whatweb_job_id': whatweb_job.id,
        'status': 'running'
    }


def web_app_audit(target, user_id, sqli_url=None, cookie=None):
    """
    Web application audit: WhatWeb → ZAP → SQLmap

    Workflow logic:
    1. WhatWeb: Fingerprint web technologies
    2. ZAP: Active web vulnerability scan (XSS, CSRF, headers...)
    3. SQLmap: SQL injection detection

    NOTE: ZAP active scan without an authentication cookie is limited to
    publicly reachable pages — this is an inherent limitation of unauthenticated
    scanning, not a bug. Pass `cookie` for authenticated app sections.

    Args:
        target: IP or domain (e.g., "192.168.200.133")
        user_id: UUID of the user
        sqli_url: Optional specific URL for SQLmap (e.g. a known injectable
                  parameter). Defaults to a generic guess based on `target`
                  if not provided — adjust per real application structure.
        cookie: Optional session cookie string for ZAP authenticated scanning
                (e.g. "PHPSESSID=abc123; security=low")

    Returns:
        dict with job_ids
    """
    whatweb_job = Job(
        id=str(uuid.uuid4()),
        user_id=user_id,
        plugin_name='whatweb',
        config={
            'target': f'http://{target}',
            'aggression': 1
        },
        status='pending'
    )

    zap_config = {
        'target': f'http://{target}',
        'scan_mode': 'active',
        'api_key': 'changeme123'
    }
    if cookie:
        zap_config['cookie'] = cookie

    zap_job = Job(
        id=str(uuid.uuid4()),
        user_id=user_id,
        plugin_name='zap',
        config=zap_config,
        status='pending'
    )

    sqlmap_target = sqli_url or f'http://{target}/?id=1'
    sqlmap_job = Job(
        id=str(uuid.uuid4()),
        user_id=user_id,
        plugin_name='sqlmap',
        config={
            'target': sqlmap_target,
            'mode': 'detect',
            'level': 1,
            'risk': 1
        },
        status='pending'
    )

    db.session.add(whatweb_job)
    db.session.add(zap_job)
    db.session.add(sqlmap_job)
    db.session.commit()

    logger.info(f"Web app audit: WhatWeb ({whatweb_job.id}) → ZAP ({zap_job.id}) → SQLmap ({sqlmap_job.id})")

    whatweb_task = run_plugin.si(whatweb_job.id, 'whatweb', whatweb_job.config)
    zap_task     = run_plugin.si(zap_job.id,     'zap',     zap_job.config)
    sqlmap_task  = run_plugin.si(sqlmap_job.id,  'sqlmap',  sqlmap_job.config)

    workflow = chain(whatweb_task, zap_task, sqlmap_task)
    result = workflow.apply_async()

    return {
        'workflow_id': str(result.id),
        'whatweb_job_id': whatweb_job.id,
        'zap_job_id': zap_job.id,
        'sqlmap_job_id': sqlmap_job.id,
        'status': 'running'
    }
