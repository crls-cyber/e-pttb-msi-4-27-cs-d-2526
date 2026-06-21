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
