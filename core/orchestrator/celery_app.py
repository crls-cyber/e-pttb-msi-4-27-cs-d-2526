"""Celery application configuration."""
import os
from celery import Celery
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Redis broker URL
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Database URL for result backend
POSTGRES_USER = os.getenv('POSTGRES_USER', 'pentest')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'password')
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
POSTGRES_DB = os.getenv('POSTGRES_DB', 'pentest_toolbox')

DATABASE_URL = f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}'

# Create Celery app
celery_app = Celery(
    'pentest_toolbox',
    broker=REDIS_URL,
    backend=f'db+{DATABASE_URL}',
    include=['core.orchestrator.tasks']
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    task_soft_time_limit=3300,  # Soft limit at 55 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
)

# Define task routes (queues)
celery_app.conf.task_routes = {
    'core.orchestrator.tasks.run_plugin': {'queue': 'scan'},
    'core.orchestrator.tasks.*': {'queue': 'default'},
}
