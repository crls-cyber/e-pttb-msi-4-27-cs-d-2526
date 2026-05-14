"""MinIO storage utilities."""
from minio import Minio
import os
from datetime import timedelta

# MinIO client
minio_client = Minio(
    os.getenv('MINIO_ENDPOINT', 'minio:9000'),
    access_key=os.getenv('MINIO_ROOT_USER', 'minioadmin'),
    secret_key=os.getenv('MINIO_ROOT_PASSWORD', 'minioadmin'),
    secure=False
)

BUCKET_NAME = 'artifacts'

# Ensure bucket exists
try:
    if not minio_client.bucket_exists(BUCKET_NAME):
        minio_client.make_bucket(BUCKET_NAME)
except Exception as e:
    print(f"MinIO bucket check failed: {e}")


def upload_artifact(filepath: str, job_id: str, filename: str) -> str:
    """
    Upload artifact to MinIO.
    
    Args:
        filepath: Local file path
        job_id: Job UUID
        filename: Original filename
        
    Returns:
        MinIO object key
    """
    object_key = f"{job_id}/{filename}"
    
    minio_client.fput_object(
        BUCKET_NAME,
        object_key,
        filepath
    )
    
    return object_key


def get_artifact_url(object_key: str, expiry: int = 3600) -> str:
    """
    Get presigned URL for artifact download.
    
    Args:
        object_key: MinIO object key
        expiry: URL expiry in seconds (default 1 hour)
        
    Returns:
        Presigned URL
    """
    url = minio_client.presigned_get_object(
        BUCKET_NAME,
        object_key,
        expires=timedelta(seconds=expiry)
    )
    
    return url
