"""
PDF Report Generator
"""
from weasyprint import HTML
from datetime import datetime
import os
from jinja2 import Environment, FileSystemLoader


def generate_pdf_report(job_id):
    """
    Generate PDF report for a job
    
    Args:
        job_id: UUID of the job
        
    Returns:
        bytes: PDF content
    """
    from core.models.job import Job
    from core.models.finding import Finding
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
        
        # Convert HTML to PDF (CSS inclus dans le HTML)
        pdf_bytes = HTML(string=html_content).write_pdf()
        
        return pdf_bytes
