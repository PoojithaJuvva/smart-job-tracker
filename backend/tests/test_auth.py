def test_register_success(client):
    response = client.post(
        "/api/auth/register",
        json={"name": "Poojitha", "email": "poo@example.com", "password": "SecurePass123"},
    )
    body = response.get_json()
    assert response.status_code == 201
    assert body["user"]["email"] == "poo@example.com"
    assert "access_token" in body
    assert "refresh_token" in body


def test_register_duplicate_email_rejected(client, registered_user):
    response = client.post(
        "/api/auth/register",
        json={"name": "Someone Else", "email": "poojitha@example.com", "password": "AnotherPass1"},
    )
    assert response.status_code == 409


def test_register_missing_fields_returns_422(client):
    response = client.post("/api/auth/register", json={"email": "bad@example.com"})
    assert response.status_code == 422
    assert "errors" in response.get_json()


def test_register_invalid_email_rejected(client):
    response = client.post(
        "/api/auth/register",
        json={"name": "Bad Email", "email": "not-an-email", "password": "SecurePass123"},
    )
    assert response.status_code == 422


def test_login_success(client, registered_user):
    response = client.post(
        "/api/auth/login",
        json={"email": "poojitha@example.com", "password": "SecurePass123"},
    )
    assert response.status_code == 200
    assert "access_token" in response.get_json()


def test_login_wrong_password_rejected(client, registered_user):
    response = client.post(
        "/api/auth/login",
        json={"email": "poojitha@example.com", "password": "WrongPassword"},
    )
    assert response.status_code == 401


def test_login_unknown_email_rejected(client):
    response = client.post(
        "/api/auth/login",
        json={"email": "ghost@example.com", "password": "whatever123"},
    )
    assert response.status_code == 401


def test_me_requires_token(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_me_returns_current_user(client, auth_headers):
    response = client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json()["email"] == "poojitha@example.com"


def test_refresh_issues_new_access_token(client, registered_user):
    refresh_token = registered_user["refresh_token"]
    response = client.post(
        "/api/auth/refresh", headers={"Authorization": f"Bearer {refresh_token}"}
    )
    assert response.status_code == 200
    assert "access_token" in response.get_json()
