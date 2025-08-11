# tests/test_app.py

import sys
import os

# Permet d'importer l'application depuis le dossier parent
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db, User, Secret
import pytest


@pytest.fixture
def client():
    # Configuration pour les tests
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # Base temporaire
    app.config['SECRET_KEY'] = 'testkey'

    with app.app_context():
        db.create_all()

    with app.test_client() as client:
        yield client

    # Nettoyage après le test
    with app.app_context():
        db.drop_all()


def test_index_redirect(client):
    """Test que l'accès à / redirige vers /login si non connecté"""
    response = client.get('/', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.headers['Location']


def test_login_page(client):
    """Test que la page de login s'affiche"""
    response = client.get('/login')
    assert response.status_code == 200
    assert b'Login' in response.data


def test_register_user(client):
    """Test l'inscription d'un nouvel utilisateur"""
    response = client.post('/register', data={
        'username': 'testuser',
        'password': 'testpass123'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Your account has been created!' in response.data


def test_login_success(client):
    """Test une connexion réussie"""
    # D'abord, inscris un utilisateur
    client.post('/register', data={
        'username': 'testuser',
        'password': 'testpass123'
    })

    # Puis connecte-toi
    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'testpass123'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'You have been logged in!' in response.data
    assert b'Add New Secret' in response.data  # On est sur la page d'accueil


def test_login_failure(client):
    """Test une connexion échouée (mauvais mot de passe)"""
    # Inscris un utilisateur
    client.post('/register', data={
        'username': 'testuser',
        'password': 'testpass123'
    })

    # Essaye de te connecter avec un mauvais mot de passe
    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'wrongpass'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Login Unsuccessful' in response.data


def test_add_secret(client):
    """Test l'ajout d'un secret après connexion"""
    # Crée et connecte un utilisateur
    client.post('/register', data={
        'username': 'testuser',
        'password': 'testpass123'
    })

    client.post('/login', data={
        'username': 'testuser',
        'password': 'testpass123'
    })

    # Ajoute un secret
    response = client.post('/add', data={
        'name': 'api-key',
        'value': 'abc123xyz'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Secret &#39;api-key&#39; added successfully!' in response.data


def test_delete_secret(client):
    """Test la suppression d'un secret"""
    # Crée utilisateur et connecte
    client.post('/register', data={
        'username': 'testuser',
        'password': 'testpass123'
    })

    client.post('/login', data={
        'username': 'testuser',
        'password': 'testpass123'
    })

    # Ajoute un secret
    client.post('/add', data={
        'name': 'old-key',
        'value': '123'
    })

    # Supprime
    response = client.get('/delete/1', follow_redirects=True)
    assert response.status_code == 200
    assert b'Secret &#39;old-key&#39; deleted successfully!' in response.data


def test_search_secrets(client):
    """Test la recherche de secrets"""
    # Crée utilisateur et connecte
    client.post('/register', data={
        'username': 'testuser',
        'password': 'testpass123'
    })

    client.post('/login', data={
        'username': 'testuser',
        'password': 'testpass123'
    })

    # Ajoute un secret
    client.post('/add', data={
        'name': 'GitHub Token',
        'value': 'secret123'
    })

    # Recherche
    response = client.get('/?query=GitHub')
    assert response.status_code == 200
    assert b'GitHub Token' in response.data


def test_logout(client):
    """Test la déconnexion"""
    # Inscris et connecte
    client.post('/register', data={
        'username': 'testuser',
        'password': 'testpass123'
    })

    client.post('/login', data={
        'username': 'testuser',
        'password': 'testpass123'
    })

    # Déconnecte
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'You have been logged out.' in response.data
    assert b'Login' in response.data  # Retour à la page de login
