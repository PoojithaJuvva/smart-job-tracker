import pytest
from app import create_app
from app.extensions import db as _db


@pytest.fixture()
def app():
    application = create_app("testing")
    with application.app_context():
        _db.create_all()
        yield application
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def registered_user(client):
    payload = {"name": "Poojitha", "email": "poojitha@example.com", "password": "SecurePass123"}
    response = client.post("/api/auth/register", json=payload)
    return response.get_json()


@pytest.fixture()
def auth_headers(registered_user):
    token = registered_user["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def sample_application(client, auth_headers):
    payload = {
        "company": "Amazon",
        "role": "SDE Intern",
        "status": "Applied",
        "location": "Hyderabad",
    }
    response = client.post("/api/applications", json=payload, headers=auth_headers)
    return response.get_json()
