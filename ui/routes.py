"""UI routes with internationalization support."""
from flask import Blueprint, render_template, redirect, url_for, request, session
from flask_login import login_required, current_user
from .i18n import get_locale, get_translations, t

ui_bp = Blueprint('ui', __name__, template_folder='templates', static_folder='static')

@ui_bp.context_processor
def inject_i18n():
    """Inject i18n functions into all templates."""
    return {
        'lang': get_locale(),
        't': t,
        'get_translations': get_translations
    }

# Redirect root to /en/dashboard
@ui_bp.route('/')
def index():
    lang = get_locale()
    return redirect(f'/{lang}/dashboard')

# Login (no lang prefix)
@ui_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Login logic here (simplified for now)
    return render_template('login.html')

# Logout (no lang prefix)
@ui_bp.route('/logout')
def logout():
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
def list_jobs():
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
    return render_template('job_new.html')

# Upload External - EN/FR
@ui_bp.route('/en/upload-external')
@ui_bp.route('/fr/upload-external')
@login_required
def upload_external():
    return render_template('upload_external.html')

# Hydra Launch - EN/FR
@ui_bp.route('/en/hydra-launch', methods=['GET'])
@ui_bp.route('/fr/hydra-launch', methods=['GET'])
@login_required
def hydra_launch():
    return render_template('hydra_launch.html')
