# tests/test_app.py

import sys
import os
import pytest

# Ajouter le dossier parent au path avant d'importer main
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app  # importe ton app Flask

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False  # si tu utilises CSRF, désactive en test
    with app.test_client() as client:
        yield client

def test_index_redirect(client):
    """Test que la page index redirige vers login si non connecté"""
    response = client.get('/', follow_redirects=False)
    assert response.status_code == 302  # redirection vers login
    assert '/login' in response.headers['Location']

def test_login_page(client):
    """Test que la page login est accessible"""
    response = client.get('/login')
    assert response.status_code == 200
    assert b'Login' in response.data  # vérifie que "Login" est dans la page
