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
