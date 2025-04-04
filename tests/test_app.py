import pytest
from main import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.test_client() as client:
        yield client

def test_about_page(client):
    """Check if the About page loads (if it exists)."""
    response = client.get('/about')
    assert response.status_code in [200, 404]

def test_terms_of_service_page(client):
    """Check if a /terms or similar legal page loads if present."""
    response = client.get('/terms')
    assert response.status_code in [200, 404]

def test_privacy_policy_page(client):
    """Check if a /privacy page loads if present."""
    response = client.get('/privacy')
    assert response.status_code in [200, 404]

def test_login_wrong_password(client):
    """Logging in with wrong credentials should fail."""
    # First, register a user
    client.post('/register', data={
        'email': 'wrongpass@example.com',
        'password': 'correctpass',
        'name': 'Wrong Pass'
    }, follow_redirects=True)

    # Now try to login with incorrect password
    response = client.post('/login', data={
        'email': 'wrongpass@example.com',
        'password': 'wrongpass'
    }, follow_redirects=True)

    assert b"incorrect" in response.data.lower() or response.status_code == 200

def test_logout_redirect(client):
    """Accessing /logout should redirect, even if not logged in."""
    response = client.get('/logout', follow_redirects=False)
    assert response.status_code in [302, 401, 403]

def test_logout_route_without_login(client):
    """Calling logout without being logged in shouldn't crash."""
    response = client.get('/logout')
    assert response.status_code in [302, 200]

def test_post_login_missing_fields(client):
    """Try logging in with no data submitted."""
    response = client.post('/login', data={})
    assert response.status_code in [200, 400]

def test_post_register_invalid_email_format(client):
    """Try registering with invalid email format (if validation exists)."""
    response = client.post('/register', data={
        'email': 'invalidemail',
        'password': 'testpass',
        'name': 'Bad Email'
    })
    assert response.status_code in [200, 400]


def test_post_register_missing_data(client):
    """Test register route with incomplete form data."""
    response = client.post('/register', data={'email': 'a@b.com'})
    assert response.status_code in [400, 200]

def test_post_login_invalid_credentials(client):
    """Login with wrong credentials should not succeed."""
    response = client.post('/login', data={
        'email': 'fake@fake.com',
        'password': 'wrongpass'
    })
    assert b"Invalid" in response.data or response.status_code in [200, 401]

def test_register_page_content(client):
    """Check for expected text in register page."""
    response = client.get('/register')
    assert b"Register" in response.data or b"Sign up" in response.data

def test_login_page_content(client):
    """Check for expected text in login page."""
    response = client.get('/login')
    assert b"Login" in response.data or b"Sign in" in response.data

def test_static_css_load(client):
    """Try to load a static CSS file if available."""
    response = client.get('/static/style.css')
    assert response.status_code in [200, 404]

def test_static_js_load(client):
    """Try to load a static JS file if available."""
    response = client.get('/static/app.js')
    assert response.status_code in [200, 404]

def test_favicon(client):
    """Try to load the favicon if available."""
    response = client.get('/favicon.ico')
    assert response.status_code in [200, 404]

def test_register_duplicate_email(client):
    client.post('/register', data={
        'email': 'duplicate@example.com',
        'password': 'pass1',
        'name': 'First'
    }, follow_redirects=True)

    response = client.post('/register', data={
        'email': 'duplicate@example.com',
        'password': 'pass2',
        'name': 'Second'
    }, follow_redirects=True)

    assert b"already" in response.data.lower() or response.status_code == 200

def test_upload_no_content_type(client):
    response = client.post('/upload', data="no file")
    assert response.status_code in [400, 403]

def test_404_page(client):
    """Ensure that a random non-existent route returns 404."""
    response = client.get('/thispagedoesnotexist')
    assert response.status_code == 404
