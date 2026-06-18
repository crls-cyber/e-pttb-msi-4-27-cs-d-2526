"""
Aggregate Report Generator — multi-job reports
Supports: global, by target, by plugin
"""
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
import os


def _get_template_env():
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    return Environment(loader=FileSystemLoader(template_dir))


def _build_stats(findings):
    return {
        'total':    len(findings),
        'critical': sum(1 for f in findings if f.severity == 'critical'),
        'high':     sum(1 for f in findings if f.severity == 'high'),
        'medium':   sum(1 for f in findings if f.severity == 'medium'),
        'low':      sum(1 for f in findings if f.severity == 'low'),
        'info':     sum(1 for f in findings if f.severity == 'info'),
    }


def _enrich_findings(findings, jobs):
    """Add plugin_name and target to each finding via job mapping."""
    job_map = {str(j.id): j for j in jobs}
    enriched = []
    for f in findings:
        job = job_map.get(str(f.job_id))
        f.plugin_name = job.plugin_name if job else 'unknown'
        f.target = job.config.get('target', job.config.get('domain', 'N/A')) if job else 'N/A'
        enriched.append(f)
    return enriched


def _sort_findings(findings):
    order = {'critical': 1, 'high': 2, 'medium': 3, 'low': 4, 'info': 5}
    return sorted(findings, key=lambda f: order.get(f.severity, 99))


def generate_global_report():
    """Generate a report aggregating ALL findings from ALL jobs."""
    from core.models.job import Job
    from core.models.finding import Finding
    from core.api.app import db

    jobs = db.session.query(Job).filter_by(status='completed').order_by(Job.created_at.desc()).all()
    job_ids = [j.id for j in jobs]
    findings = db.session.query(Finding).filter(Finding.job_id.in_(job_ids)).all()
    findings = _enrich_findings(findings, jobs)
    findings = _sort_findings(findings)

    env = _get_template_env()
    template = env.get_template('report_aggregate.html')

    return template.render(
        report_title='Global Pentest Report',
        report_subtitle=f'All completed jobs — {len(jobs)} scans — {len(findings)} findings',
        report_type='Global',
        filter_value='All completed jobs',
        jobs=jobs,
        findings=findings,
        stats=_build_stats(findings),
        generated_at=datetime.utcnow()
    )


def generate_target_report(target):
    """Generate a report for all findings on a specific target."""
    from core.models.job import Job
    from core.models.finding import Finding
    from core.api.app import db

    # Find all jobs that targeted this IP/domain
    all_jobs = db.session.query(Job).filter_by(status='completed').all()
    jobs = [j for j in all_jobs if j.config.get('target') == target or j.config.get('domain') == target]
    job_ids = [j.id for j in jobs]

    if not job_ids:
        findings = []
    else:
        findings = db.session.query(Finding).filter(Finding.job_id.in_(job_ids)).all()

    findings = _enrich_findings(findings, jobs)
    findings = _sort_findings(findings)

    env = _get_template_env()
    template = env.get_template('report_aggregate.html')

    return template.render(
        report_title='Target Report',
        report_subtitle=f'Target: {target} — {len(jobs)} scans — {len(findings)} findings',
        report_type='By Target',
        filter_value=target,
        jobs=jobs,
        findings=findings,
        stats=_build_stats(findings),
        generated_at=datetime.utcnow()
    )


def generate_plugin_report(plugin_name):
    """Generate a report for all findings from a specific plugin."""
    from core.models.job import Job
    from core.models.finding import Finding
    from core.api.app import db

    jobs = db.session.query(Job).filter_by(
        plugin_name=plugin_name,
        status='completed'
    ).order_by(Job.created_at.desc()).all()

    job_ids = [j.id for j in jobs]

    if not job_ids:
        findings = []
    else:
        findings = db.session.query(Finding).filter(Finding.job_id.in_(job_ids)).all()

    findings = _enrich_findings(findings, jobs)
    findings = _sort_findings(findings)

    env = _get_template_env()
    template = env.get_template('report_aggregate.html')

    return template.render(
        report_title='Plugin Report',
        report_subtitle=f'Plugin: {plugin_name} — {len(jobs)} runs — {len(findings)} findings',
        report_type='By Plugin',
        filter_value=plugin_name,
        jobs=jobs,
        findings=findings,
        stats=_build_stats(findings),
        generated_at=datetime.utcnow()
    )


def generate_global_pdf():
    """Generate PDF for global aggregate report."""
    from weasyprint import HTML
    html = generate_global_report()
    return HTML(string=html).write_pdf()


def generate_target_pdf(target):
    """Generate PDF for target aggregate report."""
    from weasyprint import HTML
    html = generate_target_report(target)
    return HTML(string=html).write_pdf()


def generate_plugin_pdf(plugin_name):
    """Generate PDF for plugin aggregate report."""
    from weasyprint import HTML
    html = generate_plugin_report(plugin_name)
    return HTML(string=html).write_pdf()
