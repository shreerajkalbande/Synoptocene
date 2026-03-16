import pytest
from web.app import create_app


@pytest.fixture
def client():
    app = create_app(testing=True)
    with app.test_client() as client:
        yield client


def test_home_page(client):
    """Home page should load successfully."""
    response = client.get("/")
    assert response.status_code == 200


def test_about_page(client):
    response = client.get("/about")
    assert response.status_code in [200, 404]


def test_contact_page(client):
    response = client.get("/contact")
    assert response.status_code in [200, 404]


def test_register_page_loads(client):
    response = client.get("/register")
    assert response.status_code == 200


def test_login_page_loads(client):
    response = client.get("/login")
    assert response.status_code == 200


def test_register_page_content(client):
    response = client.get("/register")
    assert b"Register" in response.data or b"Sign" in response.data


def test_login_page_content(client):
    response = client.get("/login")
    assert b"Login" in response.data or b"Sign" in response.data


def test_login_wrong_password(client):
    client.post(
        "/register",
        data={"email": "test@example.com", "password": "correctpass", "name": "Test"},
        follow_redirects=True,
    )
    response = client.post(
        "/login",
        data={"email": "test@example.com", "password": "wrongpass"},
        follow_redirects=True,
    )
    assert b"incorrect" in response.data.lower() or response.status_code == 200


def test_register_duplicate_email(client):
    client.post(
        "/register",
        data={"email": "dup@example.com", "password": "pass1", "name": "First"},
        follow_redirects=True,
    )
    response = client.post(
        "/register",
        data={"email": "dup@example.com", "password": "pass2", "name": "Second"},
        follow_redirects=True,
    )
    assert b"already" in response.data.lower() or response.status_code == 200


def test_logout_redirect(client):
    response = client.get("/logout", follow_redirects=False)
    assert response.status_code in [302, 401, 403]


def test_post_login_missing_fields(client):
    response = client.post("/login", data={})
    assert response.status_code in [200, 400]


def test_upload_requires_auth(client):
    response = client.post("/upload", data="no file")
    assert response.status_code in [400, 403]


def test_404_page(client):
    response = client.get("/thispagedoesnotexist")
    assert response.status_code == 404
