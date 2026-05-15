"""Workflows orchestration."""
import uuid
from celery import chain
from core.orchestrator.tasks import run_plugin
from core.models.job import Job
from core.api.app import db

def web_pentest_workflow(target, user_id):
    """
    Basic web pentest workflow: Nmap → Nuclei → SQLmap
    
    Args:
        target: IP or domain (e.g., "192.168.145.102")
        user_id: UUID of the user running the workflow
        
    Returns:
        Celery AsyncResult
    """
    # Create Jobs in database FIRST
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
    
    # Save to database
    db.session.add(nmap_job)
    db.session.add(nuclei_job)
    db.session.add(sqlmap_job)
    db.session.commit()
    
    # Now create Celery tasks with existing job IDs
    nmap_task = run_plugin.si(nmap_job.id, 'nmap', nmap_job.config)
    nuclei_task = run_plugin.si(nuclei_job.id, 'nuclei', nuclei_job.config)
    sqlmap_task = run_plugin.si(sqlmap_job.id, 'sqlmap', sqlmap_job.config)
    
    # Chain execution: Nmap → Nuclei → SQLmap
    workflow = chain(nmap_task, nuclei_task, sqlmap_task)
    
    return workflow.apply_async()


def recon_to_exploit_workflow(target, user_id, exploit_path=None, payload=None):
    """
    Advanced pentest workflow: Nmap → Nuclei → Metasploit (conditional)
    
    Workflow logic:
    1. Nmap: Port scan + service detection
    2. Nuclei: Vulnerability detection on discovered services
    3. Metasploit: Exploit if critical vulnerabilities found (optional)
    
    Args:
        target: IP address (e.g., "192.168.200.133")
        user_id: UUID of the user running the workflow
        exploit_path: Optional Metasploit exploit (e.g., "exploit/unix/ftp/vsftpd_234_backdoor")
        payload: Optional payload (e.g., "cmd/unix/interact")
    
    Returns:
        dict with job_ids for tracking
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Step 1: Create Nmap job
    nmap_job = Job(
        id=str(uuid.uuid4()),
        user_id=user_id,
        plugin_name='nmap',
        config={
            'target': target,
            'ports': '21,22,23,25,80,139,445,3306,5432,8080,8180'  # Common vulnerable ports
        },
        status='pending'
    )
    
    # Step 2: Create Nuclei job
    nuclei_job = Job(
        id=str(uuid.uuid4()),
        user_id=user_id,
        plugin_name='nuclei',
        config={'target': f'http://{target}'},
        status='pending'
    )
    
    # Step 3: Create Metasploit job (if exploit specified)
    metasploit_job = None
    if exploit_path and payload:
        metasploit_job = Job(
            id=str(uuid.uuid4()),
            user_id=user_id,
            plugin_name='metasploit',
            config={
                'target': target,
                'exploit': exploit_path,
                'payload': payload,
                'msf_host': '192.168.200.129',  # Adapt to your config
                'msf_password': 'msf'
            },
            status='pending'
        )
    
    # Save jobs to database
    db.session.add(nmap_job)
    db.session.add(nuclei_job)
    if metasploit_job:
        db.session.add(metasploit_job)
    db.session.commit()
    
    logger.info(f"Workflow created: Nmap ({nmap_job.id}) → Nuclei ({nuclei_job.id})" + 
                (f" → Metasploit ({metasploit_job.id})" if metasploit_job else ""))
    
    # Create Celery tasks
    nmap_task = run_plugin.si(nmap_job.id, 'nmap', nmap_job.config)
    nuclei_task = run_plugin.si(nuclei_job.id, 'nuclei', nuclei_job.config)
    
    # Chain execution
    if metasploit_job:
        metasploit_task = run_plugin.si(metasploit_job.id, 'metasploit', metasploit_job.config)
        workflow = chain(nmap_task, nuclei_task, metasploit_task)
    else:
        workflow = chain(nmap_task, nuclei_task)
    
    # Execute workflow asynchronously
    result = workflow.apply_async()
    
    return {
        'workflow_id': str(result.id),
        'nmap_job_id': nmap_job.id,
        'nuclei_job_id': nuclei_job.id,
        'metasploit_job_id': metasploit_job.id if metasploit_job else None,
        'status': 'running'
    }


def web_pentest_advanced(target, user_id, sqli_url=None):
    """
    Advanced web pentest: Nmap → Nuclei → SQLmap
    
    Args:
        target: IP or domain (e.g., "192.168.200.133")
        user_id: UUID of the user
        sqli_url: Optional specific URL for SQLmap (e.g., "http://target/page.php?id=1")
    
    Returns:
        dict with job_ids
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Step 1: Nmap web ports
    nmap_job = Job(
        id=str(uuid.uuid4()),
        user_id=user_id,
        plugin_name='nmap',
        config={
            'target': target,
            'ports': '80,443,8080,8443,8180'  # Web ports only
        },
        status='pending'
    )
    
    # Step 2: Nuclei vulnerability scan
    nuclei_job = Job(
        id=str(uuid.uuid4()),
        user_id=user_id,
        plugin_name='nuclei',
        config={'target': f'http://{target}'},
        status='pending'
    )
    
    # Step 3: SQLmap injection test
    sqlmap_target = sqli_url or f'http://{target}:8080/vulnerabilities/sqli/?id=1&Submit=Submit'
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
    
    # Save to database
    db.session.add(nmap_job)
    db.session.add(nuclei_job)
    db.session.add(sqlmap_job)
    db.session.commit()
    
    logger.info(f"Web pentest workflow: Nmap ({nmap_job.id}) → Nuclei ({nuclei_job.id}) → SQLmap ({sqlmap_job.id})")
    
    # Chain execution
    nmap_task = run_plugin.si(nmap_job.id, 'nmap', nmap_job.config)
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


def network_bruteforce(target, user_id, service='ssh', username='msfadmin', password_list=None):
    """
    Network pentest: Nmap → Hydra (brute-force)
    
    Args:
        target: IP address
        user_id: UUID of the user
        service: Service to brute-force (ssh, ftp, etc.)
        username: Username to test
        password_list: List of passwords (default: common passwords)
    
    Returns:
        dict with job_ids
    """
    import logging
    logger = logging.getLogger(__name__)
    
    if password_list is None:
        password_list = ['password', 'admin', 'msfadmin', '123456', 'root']
    
    # Step 1: Nmap common ports
    nmap_job = Job(
        id=str(uuid.uuid4()),
        user_id=user_id,
        plugin_name='nmap',
        config={
            'target': target,
            'ports': '21,22,23,25,139,445,3389'  # Auth services
        },
        status='pending'
    )
    
    # Step 2: Hydra brute-force
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
    
    # Save to database
    db.session.add(nmap_job)
    db.session.add(hydra_job)
    db.session.commit()
    
    logger.info(f"Network bruteforce workflow: Nmap ({nmap_job.id}) → Hydra ({hydra_job.id})")
    
    # Chain execution
    nmap_task = run_plugin.si(nmap_job.id, 'nmap', nmap_job.config)
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
    import logging
    logger = logging.getLogger(__name__)
    
    # Step 1: theHarvester (email, subdomains, hosts)
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
    
    # Step 2: subfinder (subdomain enumeration)
    subfinder_job = Job(
        id=str(uuid.uuid4()),
        user_id=user_id,
        plugin_name='subfinder',
        config={'domain': domain},
        status='pending'
    )
    
    # Save to database
    db.session.add(harvester_job)
    db.session.add(subfinder_job)
    db.session.commit()
    
    logger.info(f"OSINT workflow: theHarvester ({harvester_job.id}) → subfinder ({subfinder_job.id})")
    
    # Chain execution
    harvester_task = run_plugin.si(harvester_job.id, 'theharvester', harvester_job.config)
    subfinder_task = run_plugin.si(subfinder_job.id, 'subfinder', subfinder_job.config)
    
    workflow = chain(harvester_task, subfinder_task)
    result = workflow.apply_async()
    
    return {
        'workflow_id': str(result.id),
        'harvester_job_id': harvester_job.id,
        'subfinder_job_id': subfinder_job.id,
        'status': 'running'
    }
