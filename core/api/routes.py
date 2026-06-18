"""API routes."""
from core.security import audit_log, require_role
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from .auth import authenticate_user, logout_current_user
from plugins.external import WiresharkParser, MetasploitParser, AircrackParser, EttercapParser, BurpParser
from core.orchestrator import run_plugin
from core.models import Job, Finding, Artifact
from .app import db
import uuid
import os


# Auth blueprint
auth_bp = Blueprint('auth', __name__)

# API blueprint
api_bp = Blueprint('api', __name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login endpoint."""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400

    user = authenticate_user(username, password)

    if user:
        audit_log('user.login', 'user', user.id)  #  AJOUT AUDIT
        return jsonify({
            'message': 'Login successful',
            'user': {
                'id': str(user.id),
                'username': user.username
            }
        }), 200

    return jsonify({'error': 'Invalid credentials'}), 401


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """Logout endpoint."""
    logout_current_user()
    return jsonify({'message': 'Logout successful'}), 200


@api_bp.route('/users/me', methods=['GET'])
@login_required
def get_current_user_info():
    """Get current user info."""
    return jsonify({
        'id': str(current_user.id),
        'username': current_user.username,
        'email': current_user.email
    }), 200


@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'ok'}), 200


@api_bp.route('/jobs', methods=['POST'])
@login_required
def create_job():
    """Create a new job."""
    data = request.get_json()
    plugin_name = data.get('plugin')
    config = data.get('config', {})

    if not plugin_name:
        return jsonify({'error': 'Plugin name required'}), 400

    # Create job in database
    job = Job(
        id=uuid.uuid4(),
        user_id=current_user.id,
        plugin_name=plugin_name,
        config=config,
        status='pending'
    )

    db.session.add(job)
    db.session.commit()

    # Send task to Celery
    task = run_plugin.delay(str(job.id), plugin_name, config)

    audit_log('job.create', 'job', job.id)

    return jsonify({
        'job_id': str(job.id),
        'task_id': task.id,
        'status': 'pending'
    }), 201


@api_bp.route('/jobs', methods=['GET'])
@login_required
def list_jobs():
    """List user's jobs."""
    jobs = db.session.query(Job).filter_by(user_id=current_user.id).all()

    return jsonify({
        'jobs': [{
            'id': str(job.id),
            'plugin': job.plugin_name,
            'status': job.status,
            'config': job.config,
            'created_at': job.created_at.isoformat()
        } for job in jobs]
    }), 200


@api_bp.route('/jobs/<job_id>', methods=['GET'])
@login_required
def get_job(job_id):
    """Get job details."""
    job = db.session.query(Job).filter_by(id=job_id, user_id=current_user.id).first()

    if not job:
        return jsonify({'error': 'Job not found'}), 404

    return jsonify({
        'id': str(job.id),
        'plugin': job.plugin_name,
        'config': job.config,
        'status': job.status,
        'error': job.error,
        'created_at': job.created_at.isoformat(),
        'updated_at': job.updated_at.isoformat(),
        'started_at': job.started_at.isoformat() if job.started_at else None,
        'completed_at': job.completed_at.isoformat() if job.completed_at else None
    }), 200


@api_bp.route('/jobs/<job_id>/findings', methods=['GET'])
@login_required
def get_job_findings(job_id):
    """Get findings for a specific job"""
    from core.models.finding import Finding

    findings = db.session.query(Finding).filter_by(job_id=job_id).all()

    return jsonify({
        'job_id': job_id,
        'findings': [
            {
                'id': str(f.id),
                'title': f.title,
                'severity': f.severity,
                'description': f.description,
                'created_at': f.created_at.isoformat() if f.created_at else None
            }
            for f in findings
        ]
    })


@api_bp.route('/findings', methods=['GET'])
@login_required
def get_findings():
    """Get findings with optional filters"""
    from core.models.finding import Finding

    job_id = request.args.get('job_id')
    severity = request.args.get('severity')

    query = db.session.query(Finding)

    if job_id:
        query = query.filter_by(job_id=job_id)
    if severity:
        query = query.filter_by(severity=severity)

    findings = query.order_by(Finding.created_at.desc()).all()

    return jsonify([{
        'id': str(f.id),
        'job_id': str(f.job_id),
        'title': f.title,
        'severity': f.severity,
        'description': f.description,
        'cvss_score': f.cvss_score,
        'created_at': f.created_at.isoformat()
    } for f in findings])


# ============================================
# MOVED HERE: Export CSV (must be before <finding_id> route)
# ============================================
@api_bp.route('/findings/export/csv', methods=['GET'])
@login_required
def export_findings_csv():
    """Export all findings to CSV."""
    import csv
    from io import StringIO
    from flask import make_response

    # Get filters
    job_id = request.args.get('job_id')
    severity = request.args.get('severity')

    # Query findings
    from core.models import Finding

    query = db.session.query(Finding)
    if job_id:
        query = query.filter_by(job_id=job_id)
    if severity:
        query = query.filter_by(severity=severity)

    findings = query.order_by(Finding.created_at.desc()).all()

    # Create CSV
    si = StringIO()
    writer = csv.writer(si)

    # Header
    writer.writerow([
        'ID', 'Job ID', 'Title', 'Severity',
        'Description', 'CVE', 'CVSS Score',
        'Remediation', 'Created At'
    ])

    # Data
    for f in findings:
        writer.writerow([
            str(f.id),
            str(f.job_id),
            f.title,
            f.severity,
            f.description if f.description else '',
            f.cve_id or '',
            f.cvss_score or '',
            f.remediation if f.remediation else '',
            f.created_at.isoformat()
        ])

    # Response
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=findings.csv"
    output.headers["Content-type"] = "text/csv"

    return output


@api_bp.route('/findings/<finding_id>', methods=['GET'])
@login_required
def get_finding(finding_id):
    """Get a specific finding"""
    from core.models.finding import Finding

    finding = db.session.query(Finding).filter_by(id=finding_id).first_or_404()

    return jsonify({
        'id': str(finding.id),
        'job_id': str(finding.job_id),
        'title': finding.title,
        'severity': finding.severity,
        'description': finding.description,
        'cvss_score': finding.cvss_score,
        'evidence': finding.evidence,
        'remediation': finding.remediation,
        'created_at': finding.created_at.isoformat()
    })


@api_bp.route('/workflows/web-pentest', methods=['POST'])
@login_required
def run_web_pentest_workflow():
    """Launch web pentest workflow: Nmap → Nuclei → SQLmap"""
    from core.orchestrator.workflows import web_pentest_workflow

    data = request.get_json()
    target = data.get('target')

    if not target:
        return jsonify({'error': 'Target required'}), 400

    # Launch workflow
    workflow_result = web_pentest_workflow(target, current_user.id)

    audit_log('workflow.start', 'workflow', workflow_result.id)

    return jsonify({
        'workflow_id': workflow_result.id,
        'target': target,
        'status': 'running',
        'message': 'Web pentest workflow started (Nmap → Nuclei → SQLmap)'
    }), 202


@api_bp.route('/reports/<job_id>/html', methods=['GET'])
@login_required
def get_html_report(job_id):
    """Generate and return HTML report for a job"""
    from core.reporting.html_generator import generate_html_report

    try:
        html = generate_html_report(job_id)
        return html, 200, {'Content-Type': 'text/html; charset=utf-8'}
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': f'Report generation error: {str(e)}'}), 500


@api_bp.route('/reports/<job_id>/pdf', methods=['GET'])
@login_required
def get_pdf_report(job_id):
    """Generate and return PDF report for a job"""
    from core.reporting.pdf_generator import generate_pdf_report

    try:
        pdf_bytes = generate_pdf_report(job_id)

        # Create response with PDF content
        from flask import make_response
        response = make_response(pdf_bytes)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=pentest_report_{job_id[:8]}.pdf'

        return response
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': f'Report generation error: {str(e)}'}), 500


@api_bp.route('/upload-external', methods=['POST'])
@login_required
def upload_external_file():
    """Upload external file (PCAP, Metasploit logs) for parsing."""
    from werkzeug.utils import secure_filename
    import tempfile
    import shutil

    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400

    # Get parser type
    parser_type = request.form.get('parser_type', 'auto')

    # Secure filename
    filename = secure_filename(file.filename)
    ext = os.path.splitext(filename)[1].lower()

    # Auto-detect parser
    if parser_type == 'auto':
        if ext in ['.pcap', '.pcapng', '.cap']:
            parser_type = 'wireshark'
        elif ext == '.xml':
            parser_type = 'burp'
        elif ext in ['.log', '.txt']:
            parser_type = 'metasploit'
        else:
            return jsonify({'error': f'Unsupported file type: {ext}'}), 400

    # Select parser
    if parser_type == 'wireshark':
        parser = WiresharkParser()
    elif parser_type == 'metasploit':
        parser = MetasploitParser()
    elif parser_type == 'aircrack':
        parser = AircrackParser()
    elif parser_type == 'ettercap':
        parser = EttercapParser()
    elif parser_type == 'burp':
        parser = BurpParser()
    else:
        return jsonify({'error': f'Unknown parser type: {parser_type}'}), 400

    # Save to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name

    try:
        # Parse file
        result = parser.parse(tmp_path, current_user.id)

        # Create Job in database
        job = Job(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            plugin_name=f"external_{parser_type}",
            config={'filename': filename},
            status='completed'
        )
        db.session.add(job)

        # Create Findings
        for finding_data in result['findings']:
            finding = Finding(
                id=str(uuid.uuid4()),
                job_id=job.id,
                title=finding_data['title'],
                severity=finding_data['severity'],
                description=finding_data['description']
            )
            db.session.add(finding)

        # Upload original file to MinIO as artifact
        from core.storage import upload_artifact
        artifact_key = upload_artifact(tmp_path, job.id, filename)

        artifact = Artifact(
            id=str(uuid.uuid4()),
            job_id=job.id,
            filename=filename,
            content_type=file.content_type or 'application/octet-stream',
            minio_bucket='artifacts',
            minio_key=artifact_key,
            size_bytes=os.path.getsize(tmp_path)
        )
        db.session.add(artifact)

        db.session.commit()

        audit_log('external.upload', 'job', job.id)

        return jsonify({
            'success': True,
            'job_id': job.id,
            'findings_count': len(result['findings']),
            'summary': result['summary'],
            'message': f'{parser_type.capitalize()} file parsed successfully'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        # Cleanup temp file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


# ============================================
# WORKFLOWS ENDPOINTS
# ============================================

@api_bp.route('/workflows/recon-to-exploit', methods=['POST'])
@login_required
def trigger_recon_to_exploit():
    """
    Trigger recon-to-exploit workflow: Nmap -> Nuclei -> Hydra

    Request body:
    {
        "target": "192.168.200.133",
        "service": "ssh",
        "username": "admin"
    }
    """
    from core.orchestrator.workflows import recon_to_exploit_workflow
    data = request.get_json()
    if not data or 'target' not in data:
        return jsonify({'error': 'Missing required parameter: target'}), 400
    target   = data['target']
    service  = data.get('service', 'ssh')
    username = data.get('username')
    try:
        result = recon_to_exploit_workflow(
            target=target,
            user_id=current_user.id,
            service=service,
            username=username
        )
        return jsonify({
            'message': 'Recon-to-exploit workflow started (Nmap -> Nuclei -> Hydra)',
            'workflow_id': result['workflow_id'],
            'nmap_job_id': result['nmap_job_id'],
            'nuclei_job_id': result['nuclei_job_id'],
            'hydra_job_id': result['hydra_job_id'],
            'target': target,
            'stages': ['nmap', 'nuclei', 'hydra']
        }), 202
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Workflow error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/workflows/web-pentest-advanced', methods=['POST'])
@login_required
def trigger_web_pentest_advanced():
    """
    Trigger advanced web pentest: Nmap → Nuclei → SQLmap

    Request body:
    {
        "target": "192.168.200.133",
        "sqli_url": "http://192.168.200.133:8080/..."  // optional
    }
    """
    from core.orchestrator.workflows import web_pentest_advanced

    data = request.get_json()

    if not data or 'target' not in data:
        return jsonify({'error': 'Missing required parameter: target'}), 400

    target = data['target']
    sqli_url = data.get('sqli_url')

    try:
        result = web_pentest_advanced(
            target=target,
            user_id=current_user.id,
            sqli_url=sqli_url
        )

        return jsonify({
            'message': 'Web pentest workflow started',
            'workflow_id': result['workflow_id'],
            'nmap_job_id': result['nmap_job_id'],
            'nuclei_job_id': result['nuclei_job_id'],
            'sqlmap_job_id': result['sqlmap_job_id'],
            'target': target,
            'stages': ['nmap', 'nuclei', 'sqlmap']
        }), 202

    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Workflow error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/workflows/network-bruteforce', methods=['POST'])
@login_required
def trigger_network_bruteforce():
    """
    Trigger network bruteforce: Nmap → Hydra

    Request body:
    {
        "target": "192.168.200.133",
        "service": "ssh",  // optional, default: ssh
        "username": "msfadmin",  // optional
        "password_list": ["password", "admin"]  // optional
    }
    """
    from core.orchestrator.workflows import network_bruteforce

    data = request.get_json()

    if not data or 'target' not in data:
        return jsonify({'error': 'Missing required parameter: target'}), 400

    target = data['target']
    service = data.get('service', 'ssh')
    username = data.get('username', 'msfadmin')
    password_list = data.get('password_list')

    try:
        result = network_bruteforce(
            target=target,
            user_id=current_user.id,
            service=service,
            username=username,
            password_list=password_list
        )

        return jsonify({
            'message': 'Network bruteforce workflow started',
            'workflow_id': result['workflow_id'],
            'nmap_job_id': result['nmap_job_id'],
            'hydra_job_id': result['hydra_job_id'],
            'target': target,
            'stages': ['nmap', 'hydra']
        }), 202

    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Workflow error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/workflows/osint-recon', methods=['POST'])
@login_required
def trigger_osint_recon():
    """
    Trigger OSINT recon: theHarvester → subfinder

    Request body:
    {
        "domain": "example.com"
    }
    """
    from core.orchestrator.workflows import osint_recon

    data = request.get_json()

    if not data or 'domain' not in data:
        return jsonify({'error': 'Missing required parameter: domain'}), 400

    domain = data['domain']

    try:
        result = osint_recon(
            domain=domain,
            user_id=current_user.id
        )

        return jsonify({
            'message': 'OSINT recon workflow started',
            'workflow_id': result['workflow_id'],
            'harvester_job_id': result['harvester_job_id'],
            'subfinder_job_id': result['subfinder_job_id'],
            'domain': domain,
            'stages': ['theharvester', 'subfinder']
        }), 202

    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Workflow error: {str(e)}")
        return jsonify({'error': str(e)}), 500



@api_bp.route('/workflows/quick-vuln-scan', methods=['POST'])
@login_required
def trigger_quick_vuln_scan():
    """Quick vuln scan: Nmap -> Nuclei"""
    from core.orchestrator.workflows import quick_vuln_scan
    data = request.get_json()
    if not data or 'target' not in data:
        return jsonify({'error': 'Missing required parameter: target'}), 400
    target = data['target']
    try:
        result = quick_vuln_scan(target=target, user_id=current_user.id)
        return jsonify({
            'message': 'Quick vuln scan started (Nmap -> Nuclei)',
            'workflow_id': result['workflow_id'],
            'nmap_job_id': result['nmap_job_id'],
            'nuclei_job_id': result['nuclei_job_id'],
            'target': target,
            'stages': ['nmap', 'nuclei']
        }), 202
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Workflow error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/workflows/full-external-recon', methods=['POST'])
@login_required
def trigger_full_external_recon():
    """Full external recon: Subfinder -> theHarvester -> Nmap -> WhatWeb"""
    from core.orchestrator.workflows import full_external_recon
    data = request.get_json()
    if not data or 'domain' not in data:
        return jsonify({'error': 'Missing required parameter: domain'}), 400
    domain = data['domain']
    try:
        result = full_external_recon(domain=domain, user_id=current_user.id)
        return jsonify({
            'message': 'Full external recon started',
            'workflow_id': result['workflow_id'],
            'subfinder_job_id': result['subfinder_job_id'],
            'harvester_job_id': result['harvester_job_id'],
            'nmap_job_id': result['nmap_job_id'],
            'whatweb_job_id': result['whatweb_job_id'],
            'domain': domain,
            'stages': ['subfinder', 'theharvester', 'nmap', 'whatweb']
        }), 202
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Workflow error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/workflows/web-app-audit', methods=['POST'])
@login_required
def trigger_web_app_audit():
    """Web app audit: WhatWeb -> ZAP -> SQLmap"""
    from core.orchestrator.workflows import web_app_audit
    data = request.get_json()
    if not data or 'target' not in data:
        return jsonify({'error': 'Missing required parameter: target'}), 400
    target = data['target']
    try:
        result = web_app_audit(target=target, user_id=current_user.id)
        return jsonify({
            'message': 'Web app audit started (WhatWeb -> ZAP -> SQLmap)',
            'workflow_id': result['workflow_id'],
            'whatweb_job_id': result['whatweb_job_id'],
            'zap_job_id': result['zap_job_id'],
            'sqlmap_job_id': result['sqlmap_job_id'],
            'target': target,
            'stages': ['whatweb', 'zap', 'sqlmap']
        }), 202
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Workflow error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/targets', methods=['GET'])
@login_required
def list_targets():
    """List user targets."""
    from core.models.target import Target
    targets = db.session.query(Target).filter_by(user_id=current_user.id).order_by(Target.created_at.desc()).all()
    return jsonify({
        'targets': [{
            'id': str(t.id),
            'ip_or_domain': t.ip_or_domain,
            'description': t.description or '',
            'authorized': t.authorized,
            'notes': t.notes or '',
            'created_at': t.created_at.isoformat() if t.created_at else None
        } for t in targets]
    }), 200


@api_bp.route('/targets', methods=['POST'])
@login_required
def create_target():
    """Create a new target."""
    from core.models.target import Target
    data = request.get_json()
    if not data or 'ip_or_domain' not in data:
        return jsonify({'error': 'Missing required parameter: ip_or_domain'}), 400
    target = Target(
        user_id=current_user.id,
        ip_or_domain=data['ip_or_domain'].strip(),
        description=data.get('description', ''),
        authorized=data.get('authorized', True),
        notes=data.get('notes', '')
    )
    db.session.add(target)
    db.session.commit()
    audit_log('target.create', 'target', str(target.id))
    return jsonify({'id': str(target.id), 'message': 'Target created'}), 201


@api_bp.route('/targets/<target_id>', methods=['DELETE'])
@login_required
def delete_target(target_id):
    """Delete a target."""
    from core.models.target import Target
    target = db.session.query(Target).filter_by(id=target_id, user_id=current_user.id).first()
    if not target:
        return jsonify({'error': 'Target not found'}), 404
    db.session.delete(target)
    db.session.commit()
    audit_log('target.delete', 'target', target_id)
    return jsonify({'message': 'Target deleted'}), 200


@api_bp.route('/targets/<target_id>', methods=['PUT'])
@login_required
def update_target(target_id):
    """Update a target."""
    from core.models.target import Target
    target = db.session.query(Target).filter_by(id=target_id, user_id=current_user.id).first()
    if not target:
        return jsonify({'error': 'Target not found'}), 404
    data = request.get_json()
    if 'ip_or_domain' in data:  target.ip_or_domain = data['ip_or_domain'].strip()
    if 'description'  in data:  target.description  = data['description']
    if 'authorized'   in data:  target.authorized   = data['authorized']
    if 'notes'        in data:  target.notes        = data['notes']
    db.session.commit()
    audit_log('target.update', 'target', target_id)
    return jsonify({'message': 'Target updated'}), 200


@api_bp.route('/reports/global', methods=['GET'])
@login_required
def get_global_report():
    """Generate global aggregate report — all completed jobs."""
    try:
        from core.reporting.aggregate_report_generator import generate_global_report
        html = generate_global_report()
        return html, 200, {'Content-Type': 'text/html; charset=utf-8'}
    except Exception as e:
        return jsonify({'error': f'Report generation error: {str(e)}'}), 500


@api_bp.route('/reports/target/<path:target>', methods=['GET'])
@login_required
def get_target_report(target):
    """Generate report for all findings on a specific target."""
    try:
        from core.reporting.aggregate_report_generator import generate_target_report
        html = generate_target_report(target)
        return html, 200, {'Content-Type': 'text/html; charset=utf-8'}
    except Exception as e:
        return jsonify({'error': f'Report generation error: {str(e)}'}), 500


@api_bp.route('/reports/plugin/<plugin_name>', methods=['GET'])
@login_required
def get_plugin_report(plugin_name):
    """Generate report for all findings from a specific plugin."""
    try:
        from core.reporting.aggregate_report_generator import generate_plugin_report
        html = generate_plugin_report(plugin_name)
        return html, 200, {'Content-Type': 'text/html; charset=utf-8'}
    except Exception as e:
        return jsonify({'error': f'Report generation error: {str(e)}'}), 500

@api_bp.route('/stats/dashboard', methods=['GET'])
@login_required
def get_dashboard_stats():
    '''
    Get dashboard statistics

    Returns:
    - findings_by_severity: {critical: N, high: N, ...}
    - jobs_by_status: {completed: N, running: N, failed: N}
    - recent_jobs: [last 10 jobs]
    - top_plugins: [most used plugins]
    '''
    from sqlalchemy import func

    # Findings by severity
    findings_by_severity = db.session.query(
        Finding.severity,
        func.count(Finding.id).label('count')
    ).group_by(Finding.severity).all()

    findings_stats = {sev: count for sev, count in findings_by_severity}

    # Jobs by status
    jobs_by_status = db.session.query(
        Job.status,
        func.count(Job.id).label('count')
    ).group_by(Job.status).all()

    jobs_stats = {status: count for status, count in jobs_by_status}

    # Recent jobs (last 10)
    recent_jobs = db.session.query(Job).order_by(
        Job.created_at.desc()
    ).limit(10).all()

    recent_jobs_data = [{
        'id': str(job.id),
        'plugin': job.plugin_name,
        'status': job.status,
        'created_at': job.created_at.isoformat() if job.created_at else None
    } for job in recent_jobs]

    # Top plugins used
    top_plugins = db.session.query(
        Job.plugin_name,
        func.count(Job.id).label('count')
    ).group_by(Job.plugin_name).order_by(
        func.count(Job.id).desc()
    ).limit(5).all()

    top_plugins_data = {plugin: count for plugin, count in top_plugins}

    return jsonify({
        'findings_by_severity': findings_stats,
        'jobs_by_status': jobs_stats,
        'recent_jobs': recent_jobs_data,
        'top_plugins': top_plugins_data
    })
