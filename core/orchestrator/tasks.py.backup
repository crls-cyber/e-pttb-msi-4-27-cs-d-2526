"""Celery tasks."""
from .celery_app import celery_app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.models import Job, Finding
from core.plugins import executor
import os
from dotenv import load_dotenv
import uuid

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
        session.commit()
        
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

