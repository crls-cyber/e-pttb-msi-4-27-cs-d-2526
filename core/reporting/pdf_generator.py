"""
PDF Report Generator with MinIO persistence
"""
from weasyprint import HTML
from datetime import datetime
import os
import tempfile
import uuid
from jinja2 import Environment, FileSystemLoader


def generate_pdf_report(job_id, save_to_minio=True):
    """
    Generate PDF report for a job and optionally save to MinIO
    
    Args:
        job_id: UUID of the job
        save_to_minio: If True, upload to MinIO and create Artifact entry
    
    Returns:
        bytes: PDF content
    """
    from core.models.job import Job
    from core.models.finding import Finding
    from core.models.artifact import Artifact
    from core.api.app import create_app
    
    # Create Flask app context
    app = create_app()
    
    with app.app_context():
        from core.api.app import db
        
        # Get job from database
        job = db.session.query(Job).filter_by(id=job_id).first()
        
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        # Get findings for this job
        findings = db.session.query(Finding).filter_by(job_id=job_id).order_by(
            Finding.severity.desc(),
            Finding.created_at.desc()
        ).all()
        
        # Group by severity
        findings_by_severity = {
            'critical': [f for f in findings if f.severity == 'critical'],
            'high': [f for f in findings if f.severity == 'high'],
            'medium': [f for f in findings if f.severity == 'medium'],
            'low': [f for f in findings if f.severity == 'low']
        }
        
        # Calculate statistics
        stats = {
            'total': len(findings),
            'critical': len(findings_by_severity['critical']),
            'high': len(findings_by_severity['high']),
            'medium': len(findings_by_severity['medium']),
            'low': len(findings_by_severity['low'])
        }
        
        # Load Jinja2 template
        template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template('report_pdf.html')
        
        # Render template with data
        html_content = template.render(
            job=job,
            findings=findings,
            findings_by_severity=findings_by_severity,
            stats=stats,
            generated_at=datetime.utcnow()
        )
        
        # Convert HTML to PDF
        pdf_bytes = HTML(string=html_content).write_pdf()
        
        # Upload to MinIO if requested
        if save_to_minio:
            from core.storage import upload_artifact
            
            # Check if artifact already exists for this job (type: application/pdf)
            existing = db.session.query(Artifact).filter_by(
                job_id=job_id,
                content_type='application/pdf'
            ).first()
            
            if not existing:
                # Save to temporary file
                with tempfile.NamedTemporaryFile(mode='wb', suffix='.pdf', delete=False) as tmp:
                    tmp.write(pdf_bytes)
                    tmp_path = tmp.name
                
                try:
                    # Upload to MinIO
                    filename = f'report_{str(job_id)[:8]}.pdf'
                    artifact_key = upload_artifact(tmp_path, job_id, filename)
                    
                    # Create Artifact entry in database
                    artifact = Artifact(
                        id=str(uuid.uuid4()),
                        job_id=job_id,
                        filename=filename,
                        content_type='application/pdf',
                        minio_bucket='artifacts',
                        minio_key=artifact_key,
                        size_bytes=len(pdf_bytes)
                    )
                    db.session.add(artifact)
                    db.session.commit()
                    
                finally:
                    # Cleanup temp file
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
        
        return pdf_bytes
