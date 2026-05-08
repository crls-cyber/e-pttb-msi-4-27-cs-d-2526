"""Celery tasks."""
from .celery_app import celery_app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.models import Job
import os
from dotenv import load_dotenv

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
        
        # TODO: Load and execute the plugin (Jour 4)
        # For now, just simulate work
        import time
        time.sleep(5)
        
        # Update job status to completed
        job.status = 'completed'
        session.commit()
        
        return {
            'job_id': str(job_id),
            'plugin': plugin_name,
            'status': 'completed'
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
