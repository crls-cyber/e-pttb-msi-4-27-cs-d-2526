"""
Tests unitaires des routes UI Flask
"""
import pytest


def test_index_redirect_to_login(client):
    """Test: / redirige vers /login si non authentifié"""
    response = client.get('/')
    assert response.status_code == 302
    assert '/login' in response.location


def test_login_page_loads(client):
    """Test: Page login se charge correctement"""
    response = client.get('/login')
    assert response.status_code == 200
    assert b'Connexion' in response.data


def test_dashboard_requires_auth(client):
    """Test: Dashboard nécessite authentification"""
    response = client.get('/dashboard')
    assert response.status_code == 302
    assert '/login' in response.location


def test_dashboard_loads_when_authenticated(auth_client, db):
    """Test: Dashboard se charge si authentifié"""
    response = auth_client.get('/dashboard')
    assert response.status_code == 200
    assert b'Dashboard' in response.data
    assert b'Bienvenue' in response.data


def test_jobs_list_requires_auth(client):
    """Test: Liste jobs nécessite authentification"""
    response = client.get('/jobs')
    assert response.status_code == 302


def test_jobs_list_loads_when_authenticated(auth_client):
    """Test: Liste jobs se charge si authentifié"""
    response = auth_client.get('/jobs')
    assert response.status_code == 200
    assert b'Jobs' in response.data


def test_new_job_form_loads(auth_client):
    """Test: Formulaire nouveau scan se charge"""
    response = auth_client.get('/jobs/new')
    assert response.status_code == 200
    assert b'Nouveau Scan' in response.data
    assert b'nmap' in response.data
    assert b'nuclei' in response.data
    assert b'sqlmap' in response.data


def test_job_detail_loads(auth_client, sample_job):
    """Test: Page détails job se charge"""
    response = auth_client.get(f'/jobs/{sample_job.id}')
    assert response.status_code == 200
    assert b'Job' in response.data
    assert sample_job.plugin_name.encode() in response.data
