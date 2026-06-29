"""UI routes for the Pentest Toolbox."""
from flask import Blueprint, render_template, request, redirect, session
from flask_login import login_required, login_user, logout_user, current_user
from ui.i18n import get_locale, get_translations

ui_bp = Blueprint('ui', __name__, template_folder='templates', static_folder='static', static_url_path='/static')

@ui_bp.context_processor
def inject_i18n():
    """Inject i18n functions into all templates."""
    from ui.i18n import t
    return {
        'lang': get_locale(),
        't': t,
        'get_translations': get_translations
    }

@ui_bp.before_request
def enforce_password_change():
    """Force redirect to /settings if user must change their password."""
    if current_user.is_authenticated and getattr(current_user, 'must_change_password', False):
        allowed_endpoints = ('ui.settings', 'ui.logout', 'static')
        if request.endpoint not in allowed_endpoints:
            lang = get_locale()
            return redirect(f'/{lang}/settings?force_password_change=1')


@ui_bp.route('/')
def root():
    """Redirect root to login if not authenticated, else to dashboard."""
    from flask_login import current_user
    if current_user.is_authenticated:
        lang = get_locale()
        return redirect(f'/{lang}/dashboard')
    return redirect('/login')

@ui_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page and authentication."""
    if request.method == 'POST':
        from core.models import User
        from core.api.app import db
        from werkzeug.security import check_password_hash
        
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            return render_template('login.html', error='Missing username or password')
        
        # Find user
        user = db.session.query(User).filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            lang = get_locale()
            # Force password change on first login
            if user.must_change_password:
                return redirect(f'/{lang}/settings?force_password_change=1')
            # Redirect to dashboard
            return redirect(f'/{lang}/dashboard')
        else:
            return render_template('login.html', error='Invalid username or password')
    
    return render_template('login.html')

@ui_bp.route('/logout')
def logout():
    """Logout and clear session."""
    logout_user()
    session.clear()
    return redirect('/login')

# Dashboard - EN/FR
@ui_bp.route('/en/dashboard')
@ui_bp.route('/fr/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

# Jobs List - EN/FR
@ui_bp.route('/en/jobs')
@ui_bp.route('/fr/jobs')
@login_required
def jobs():
    return render_template('jobs.html')

# Job Detail - EN/FR
@ui_bp.route('/en/jobs/<job_id>')
@ui_bp.route('/fr/jobs/<job_id>')
@login_required
def job_detail(job_id):
    return render_template('job_detail.html', job_id=job_id)

# New Job - EN/FR
@ui_bp.route('/en/jobs/new', methods=['GET', 'POST'])
@ui_bp.route('/fr/jobs/new', methods=['GET', 'POST'])
@login_required
def new_job():
    if request.method == 'POST':
        from core.models import Job
        from core.api.app import db
        from core.orchestrator.tasks import run_plugin
        import uuid
        from datetime import datetime
        from flask import flash
        
        # Récupérer les données du formulaire
        plugin = request.form.get('plugin')
        target = request.form.get('target')
        
        if not plugin or not target:
            flash('Plugin and target are required', 'error')
            return render_template('new_job.html')
        
        # Construire la config selon le plugin
        config = {'target': target}
        
        # Options spécifiques par plugin
        if plugin == 'nmap':
            if request.form.get('ports'):
                config['ports'] = request.form.get('ports')
            if request.form.get('scan_type'):
                config['scan_type'] = request.form.get('scan_type')
        
        elif plugin == 'nuclei':
            if request.form.get('severity'):
                config['severity'] = request.form.get('severity')
        
        elif plugin == 'sqlmap':
            if request.form.get('mode'):
                config['mode'] = request.form.get('mode')
            config['url'] = target  # SQLmap needs 'url' not 'target'
        
        elif plugin == 'hydra':
            if request.form.get('service'):
                config['service'] = request.form.get('service')
            if request.form.get('username'):
                config['username'] = request.form.get('username')
            # Si password fourni, l'utiliser, sinon utiliser passlist par défaut
            password = request.form.get('password')
            if password:
                config['password'] = password
            else:
                config['passlist'] = '/usr/share/wordlists/rockyou.txt'  # Wordlist par défaut
        
        elif plugin == 'subfinder':
            config['domain'] = target  # subfinder attend 'domain' pas 'target'
        
        elif plugin == 'theharvester':
            config['domain'] = target  # theHarvester attend aussi 'domain'
        
        # Créer le job directement en BDD
        try:
            job = Job(
                id=uuid.uuid4(),
                user_id=current_user.id,
                plugin_name=plugin,
                config=config,
                status='pending',
                created_at=datetime.utcnow()
            )
            
            db.session.add(job)
            db.session.commit()
            
            # Lancer la tâche Celery
            run_plugin.delay(str(job.id), plugin, config)
            
            flash(f'Job created successfully! ID: {job.id}', 'success')
            lang = get_locale()
            return redirect(f'/{lang}/jobs/{job.id}')
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating job: {str(e)}', 'error')
            return render_template('new_job.html')
    
    return render_template('new_job.html')

@ui_bp.route('/en/findings')
@ui_bp.route('/fr/findings')
@login_required
def findings():
    return render_template('findings.html')

# Workflows - EN/FR
@ui_bp.route('/en/workflows')
@ui_bp.route('/fr/workflows')
@login_required
def workflows():
    return render_template('workflows.html')

# Upload - EN/FR
@ui_bp.route('/en/upload-external')
@ui_bp.route('/fr/upload-external')
@login_required
def upload_external():
    return render_template('upload_external.html')

# ==========================================
# PHASE 1 - PLACEHOLDER ROUTES (UI-FIRST)
# ==========================================

@ui_bp.route('/en/projects')
@ui_bp.route('/fr/projects')
@login_required
def projects():
    return render_template('projects.html')

@ui_bp.route('/en/targets')
@ui_bp.route('/fr/targets')
@login_required
def targets():
    return render_template('targets.html')

@ui_bp.route('/en/reports')
@ui_bp.route('/fr/reports')
@login_required
def reports():
    return render_template('reports.html')

@ui_bp.route('/en/integrations')
@ui_bp.route('/fr/integrations')
@login_required
def integrations():
    return render_template('integrations.html')

@ui_bp.route('/en/compliance')
@ui_bp.route('/fr/compliance')
@login_required
def compliance():
    return render_template('compliance.html')

@ui_bp.route('/en/analytics')
@ui_bp.route('/fr/analytics')
@login_required
def analytics():
    return render_template('analytics.html')

@ui_bp.route('/en/settings')
@ui_bp.route('/fr/settings')
@login_required
def settings():
    return render_template('settings.html')

# ==========================================
# PLUGIN DEDICATED LAUNCH PAGES
# ==========================================

# Nmap dedicated launch page
@ui_bp.route('/en/jobs/new/nmap', methods=['GET', 'POST'])
@ui_bp.route('/fr/jobs/new/nmap', methods=['GET', 'POST'])
@login_required
def nmap_launch():
    if request.method == 'POST':
        from core.models import Job
        from core.api.app import db
        from core.orchestrator.tasks import run_plugin
        import uuid
        from datetime import datetime
        from flask import flash

        target = request.form.get('target')
        if target:
            from core.security.scope_checker import enforce_scope, ScopeViolation
            try:
                enforce_scope(target)
            except ScopeViolation as e:
                flash(str(e), 'error')
                return render_template('nmap_launch.html')
        if not target:
            flash('Target is required', 'error')
            return render_template('nmap_launch.html')

        config = {'target': target}
        if request.form.get('ports'):
            config['ports'] = request.form.get('ports')
        if request.form.get('scan_type'):
            config['scan_type'] = request.form.get('scan_type')
        if request.form.get('timing'):
            config['timing'] = request.form.get('timing')
        if request.form.get('enable_os_detection'):
            config['os_detection'] = True
        if request.form.get('enable_script_scan'):
            config['script_scan'] = True
        if request.form.get('aggressive_scan'):
            config['aggressive'] = True
        if request.form.get('custom_args'):
            config['custom_args'] = request.form.get('custom_args')

        try:
            job = Job(
                id=uuid.uuid4(),
                user_id=current_user.id,
                plugin_name='nmap',
                config=config,
                status='pending',
                created_at=datetime.utcnow()
            )
            db.session.add(job)
            db.session.commit()
            run_plugin.delay(str(job.id), 'nmap', config)
            flash(f'Nmap scan launched! Job ID: {job.id}', 'success')
            lang = get_locale()
            return redirect(f'/{lang}/jobs/{job.id}')
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')
            return render_template('nmap_launch.html')

    return render_template('nmap_launch.html')

# Nuclei dedicated launch page
@ui_bp.route('/en/jobs/new/nuclei', methods=['GET', 'POST'])
@ui_bp.route('/fr/jobs/new/nuclei', methods=['GET', 'POST'])
@login_required
def nuclei_launch():
    if request.method == 'POST':
        from core.models import Job
        from core.api.app import db
        from core.orchestrator.tasks import run_plugin
        import uuid
        from datetime import datetime
        from flask import flash

        target = request.form.get('target')
        if target:
            from core.security.scope_checker import enforce_scope, ScopeViolation
            try:
                enforce_scope(target)
            except ScopeViolation as e:
                flash(str(e), 'error')
                return render_template('nuclei_launch.html')
        if not target:
            protocol = request.form.get('protocol', 'http://')
            host = request.form.get('target_host', '')
            target = protocol + host
        if not target or target in ['http://', 'https://']:
            flash('Target URL is required', 'error')
            return render_template('nuclei_launch.html')

        # Severity : construire la liste cumulative
        severity_min = request.form.get('severity', 'medium')
        severity_levels = ['critical', 'high', 'medium', 'low', 'info']
        idx = severity_levels.index(severity_min) if severity_min in severity_levels else 2
        severity_str = ','.join(severity_levels[:idx+1])

        # Templates : convertir liste en string pour -tags
        templates_list = request.form.getlist('templates')
        templates_str = ','.join(templates_list) if templates_list else ''

        config = {
            'target': target,
            'severity': severity_str,
            'templates': templates_str,
        }

        if request.form.get('concurrency'):
            config['concurrency'] = int(request.form.get('concurrency'))
        if request.form.get('rate_limit'):
            config['rate_limit'] = int(request.form.get('rate_limit'))
        if request.form.get('timeout'):
            config['timeout'] = int(request.form.get('timeout'))
        if request.form.get('headless'):
            config['headless'] = True
        if request.form.get('custom_args'):
            config['custom_args'] = request.form.get('custom_args')

        try:
            job = Job(
                id=uuid.uuid4(),
                user_id=current_user.id,
                plugin_name='nuclei',
                config=config,
                status='pending',
                created_at=datetime.utcnow()
            )
            db.session.add(job)
            db.session.commit()
            run_plugin.delay(str(job.id), 'nuclei', config)
            flash(f'Nuclei scan launched! Job ID: {job.id}', 'success')
            lang = get_locale()
            return redirect(f'/{lang}/jobs/{job.id}')
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')
            return render_template('nuclei_launch.html')

    return render_template('nuclei_launch.html')

# SQLmap dedicated launch page
@ui_bp.route('/en/jobs/new/sqlmap', methods=['GET', 'POST'])
@ui_bp.route('/fr/jobs/new/sqlmap', methods=['GET', 'POST'])
@login_required
def sqlmap_launch():
    if request.method == 'POST':
        from core.models import Job
        from core.api.app import db
        from core.orchestrator.tasks import run_plugin
        import uuid
        from datetime import datetime
        from flask import flash

        target = request.form.get('target')
        if target:
            from core.security.scope_checker import enforce_scope, ScopeViolation
            try:
                enforce_scope(target)
            except ScopeViolation as e:
                flash(str(e), 'error')
                return render_template('sqlmap_launch.html')
        if not target:
            flash('Target URL is required', 'error')
            return render_template('sqlmap_launch.html')

        config = {
            'target': target,
            'mode': request.form.get('mode', 'detect'),
            'level': int(request.form.get('level', 1)),
            'risk': int(request.form.get('risk', 1)),
        }
        if request.form.get('parameter'):
            config['parameter'] = request.form.get('parameter')
        if request.form.get('cookie'):
            config['cookie'] = request.form.get('cookie')
        if request.form.get('scan_forms'):
            config['scan_forms'] = True
        if request.form.get('headers'):
            config['headers'] = request.form.get('headers')
        if request.form.get('database'):
            config['database'] = request.form.get('database')
        if request.form.get('table'):
            config['table'] = request.form.get('table')
        if request.form.get('tor'):
            config['tor'] = True

        try:
            job = Job(
                id=uuid.uuid4(),
                user_id=current_user.id,
                plugin_name='sqlmap',
                config=config,
                status='pending',
                created_at=datetime.utcnow()
            )
            db.session.add(job)
            db.session.commit()
            run_plugin.delay(str(job.id), 'sqlmap', config)
            flash(f'SQLmap scan launched! Job ID: {job.id}', 'success')
            lang = get_locale()
            return redirect(f'/{lang}/jobs/{job.id}')
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')
            return render_template('sqlmap_launch.html')

    return render_template('sqlmap_launch.html')

# Hydra dedicated launch page
@ui_bp.route('/en/jobs/new/hydra', methods=['GET', 'POST'])
@ui_bp.route('/fr/jobs/new/hydra', methods=['GET', 'POST'])
@login_required
def hydra_launch():
    if request.method == 'POST':
        from core.models import Job
        from core.api.app import db
        from core.orchestrator.tasks import run_plugin
        import uuid
        from datetime import datetime
        from flask import flash

        target = request.form.get('target')
        if target:
            from core.security.scope_checker import enforce_scope, ScopeViolation
            try:
                enforce_scope(target)
            except ScopeViolation as e:
                flash(str(e), 'error')
                return render_template('hydra_launch.html')
        service = request.form.get('service')
        if not target or not service:
            flash('Target and service are required', 'error')
            return render_template('hydra_launch.html')

        config = {
            'target': target,
            'service': service,
            'threads': int(request.form.get('threads', 4)),
            'find_all': request.form.get('find_all') == 'true',
        }

        username = request.form.get('username')
        userlist = request.form.get('userlist')
        password = request.form.get('password')
        passlist = request.form.get('passlist')

        if username:
            config['username'] = username
        elif userlist:
            config['userlist'] = userlist
        else:
            config['username'] = 'admin'

        if password:
            config['password'] = password
        elif passlist:
            config['passlist'] = passlist
        else:
            config['passlist'] = '/usr/share/wordlists/fasttrack.txt'

        if request.form.get('port'):
            config['port'] = int(request.form.get('port'))

        try:
            job = Job(
                id=uuid.uuid4(),
                user_id=current_user.id,
                plugin_name='hydra',
                config=config,
                status='pending',
                created_at=datetime.utcnow()
            )
            db.session.add(job)
            db.session.commit()
            run_plugin.delay(str(job.id), 'hydra', config)
            flash(f'Hydra attack launched! Job ID: {job.id}', 'success')
            lang = get_locale()
            return redirect(f'/{lang}/jobs/{job.id}')
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')
            return render_template('hydra_launch.html')

    return render_template('hydra_launch.html')

# Subfinder dedicated launch page
@ui_bp.route('/en/jobs/new/subfinder', methods=['GET', 'POST'])
@ui_bp.route('/fr/jobs/new/subfinder', methods=['GET', 'POST'])
@login_required
def subfinder_launch():
    if request.method == 'POST':
        from core.models import Job
        from core.api.app import db
        from core.orchestrator.tasks import run_plugin
        import uuid
        from datetime import datetime
        from flask import flash

        domain = request.form.get('domain')
        if domain:
            from core.security.scope_checker import enforce_scope, ScopeViolation
            try:
                enforce_scope(domain)
            except ScopeViolation as e:
                flash(str(e), 'error')
                return render_template('subfinder_launch.html')
        if not domain:
            flash('Domain is required', 'error')
            return render_template('subfinder_launch.html')

        config = {
            'domain': domain,
            'timeout': int(request.form.get('timeout', 300)),
            'max_results': int(request.form.get('max_results', 1000)),
        }
        sources = request.form.getlist('sources')
        if sources:
            config['sources'] = sources

        try:
            job = Job(
                id=uuid.uuid4(),
                user_id=current_user.id,
                plugin_name='subfinder',
                config=config,
                status='pending',
                created_at=datetime.utcnow()
            )
            db.session.add(job)
            db.session.commit()
            run_plugin.delay(str(job.id), 'subfinder', config)
            flash(f'Subfinder scan launched! Job ID: {job.id}', 'success')
            lang = get_locale()
            return redirect(f'/{lang}/jobs/{job.id}')
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')
            return render_template('subfinder_launch.html')

    return render_template('subfinder_launch.html')

# theHarvester dedicated launch page
@ui_bp.route('/en/jobs/new/theharvester', methods=['GET', 'POST'])
@ui_bp.route('/fr/jobs/new/theharvester', methods=['GET', 'POST'])
@login_required
def theharvester_launch():
    if request.method == 'POST':
        from core.models import Job
        from core.api.app import db
        from core.orchestrator.tasks import run_plugin
        import uuid
        from datetime import datetime
        from flask import flash

        domain = request.form.get('domain')
        if domain:
            from core.security.scope_checker import enforce_scope, ScopeViolation
            try:
                enforce_scope(domain)
            except ScopeViolation as e:
                flash(str(e), 'error')
                return render_template('theharvester_launch.html')
        if not domain:
            flash('Domain is required', 'error')
            return render_template('theharvester_launch.html')

        config = {
            'domain': domain,
            'source': request.form.get('source', 'all'),
            'limit': int(request.form.get('limit', 500)),
        }

        try:
            job = Job(
                id=uuid.uuid4(),
                user_id=current_user.id,
                plugin_name='theharvester',
                config=config,
                status='pending',
                created_at=datetime.utcnow()
            )
            db.session.add(job)
            db.session.commit()
            run_plugin.delay(str(job.id), 'theharvester', config)
            flash(f'theHarvester scan launched! Job ID: {job.id}', 'success')
            lang = get_locale()
            return redirect(f'/{lang}/jobs/{job.id}')
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')
            return render_template('theharvester_launch.html')

    return render_template('theharvester_launch.html')

# ZAP dedicated launch page
@ui_bp.route('/en/jobs/new/zap', methods=['GET', 'POST'])
@ui_bp.route('/fr/jobs/new/zap', methods=['GET', 'POST'])
@login_required
def zap_launch():
    if request.method == 'POST':
        from core.models import Job
        from core.api.app import db
        from core.orchestrator.tasks import run_plugin
        import uuid
        from datetime import datetime
        from flask import flash

        target = request.form.get('target')
        if target:
            from core.security.scope_checker import enforce_scope, ScopeViolation
            try:
                enforce_scope(target)
            except ScopeViolation as e:
                flash(str(e), 'error')
                return render_template('zap_launch.html')
        if not target or target in ['http://', 'https://']:
            protocol = request.form.get('protocol', 'http://')
            host = request.form.get('target_host', '')
            target = protocol + host
        if not target or target in ['http://', 'https://']:
            flash('Target URL is required', 'error')
            return render_template('zap_launch.html')

        config = {
            'target': target,
            'scan_mode': request.form.get('scan_mode', 'active'),
            'timeout': int(request.form.get('timeout', 600)),
            'api_key': request.form.get('api_key', 'changeme123'),
            'cookie': request.form.get('cookie', ''),
            'spider_delay': int(request.form.get('spider_delay', 5)),
        }

        try:
            job = Job(
                id=uuid.uuid4(),
                user_id=current_user.id,
                plugin_name='zap',
                config=config,
                status='pending',
                created_at=datetime.utcnow()
            )
            db.session.add(job)
            db.session.commit()
            run_plugin.delay(str(job.id), 'zap', config)
            flash(f'ZAP scan launched! Job ID: {job.id}', 'success')
            lang = get_locale()
            return redirect(f'/{lang}/jobs/{job.id}')
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')
            return render_template('zap_launch.html')

    return render_template('zap_launch.html')

# Metasploit dedicated launch page
@ui_bp.route('/en/jobs/new/metasploit', methods=['GET'])
@ui_bp.route('/fr/jobs/new/metasploit', methods=['GET'])
@login_required
def metasploit_launch():
    return render_template('metasploit_launch.html')

# WhatWeb dedicated launch page
@ui_bp.route('/en/jobs/new/whatweb', methods=['GET', 'POST'])
@ui_bp.route('/fr/jobs/new/whatweb', methods=['GET', 'POST'])
@login_required
def whatweb_launch():
    if request.method == 'POST':
        from core.models import Job
        from core.api.app import db
        from core.orchestrator.tasks import run_plugin
        import uuid
        from datetime import datetime
        from flask import flash

        target = request.form.get('target')
        if target:
            from core.security.scope_checker import enforce_scope, ScopeViolation
            try:
                enforce_scope(target)
            except ScopeViolation as e:
                flash(str(e), 'error')
                return render_template('whatweb_launch.html')
        if not target or target in ['http://', 'https://']:
            flash('Target URL is required', 'error')
            return render_template('whatweb_launch.html')

        config = {
            'target': target,
            'aggression': int(request.form.get('aggression', 1)),
            'timeout': int(request.form.get('timeout', 60)),
        }

        try:
            job = Job(
                id=uuid.uuid4(),
                user_id=current_user.id,
                plugin_name='whatweb',
                config=config,
                status='pending',
                created_at=datetime.utcnow()
            )
            db.session.add(job)
            db.session.commit()
            run_plugin.delay(str(job.id), 'whatweb', config)
            flash(f'WhatWeb scan launched! Job ID: {job.id}', 'success')
            lang = get_locale()
            return redirect(f'/{lang}/jobs/{job.id}')
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')
            return render_template('whatweb_launch.html')

    return render_template('whatweb_launch.html')

# Aircrack dedicated page
@ui_bp.route('/en/jobs/new/aircrack', methods=['GET'])
@ui_bp.route('/fr/jobs/new/aircrack', methods=['GET'])
@login_required
def aircrack_launch():
    return render_template('aircrack_launch.html')

# Ettercap dedicated page
@ui_bp.route('/en/jobs/new/ettercap', methods=['GET'])
@ui_bp.route('/fr/jobs/new/ettercap', methods=['GET'])
@login_required
def ettercap_launch():
    return render_template('ettercap_launch.html')

# Wireshark dedicated page
@ui_bp.route('/en/jobs/new/wireshark', methods=['GET'])
@ui_bp.route('/fr/jobs/new/wireshark', methods=['GET'])
@login_required
def wireshark_launch():
    return render_template('wireshark_launch.html')

# Burp Suite dedicated page
@ui_bp.route('/en/jobs/new/burp', methods=['GET'])
@ui_bp.route('/fr/jobs/new/burp', methods=['GET'])
@login_required
def burp_launch():
    return render_template('burp_launch.html')

# Admin — user management
@ui_bp.route('/en/admin/users')
@ui_bp.route('/fr/admin/users')
@login_required
def admin_users():
    """Admin-only user management page."""
    is_admin = any(role.name == 'admin' for role in current_user.roles)
    if not is_admin:
        from flask import abort
        abort(403)
    return render_template('admin_users.html')

# Pivot Chains — data-driven workflows
@ui_bp.route('/en/pivot-chains')
@ui_bp.route('/fr/pivot-chains')
@login_required
def pivot_chains():
    """Pivot Chains — data-driven workflows page."""
    return render_template('pivot_chains.html')

# Compliance — RGPD / Authorized / Encrypted info pages
@ui_bp.route('/en/compliance/rgpd')
@ui_bp.route('/fr/compliance/rgpd')
@login_required
def compliance_rgpd():
    return render_template('compliance_rgpd.html')

@ui_bp.route('/en/compliance/authorized')
@ui_bp.route('/fr/compliance/authorized')
@login_required
def compliance_authorized():
    return render_template('compliance_authorized.html')

@ui_bp.route('/en/compliance/encrypted')
@ui_bp.route('/fr/compliance/encrypted')
@login_required
def compliance_encrypted():
    return render_template('compliance_encrypted.html')
