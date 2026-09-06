def test_create_application_requires_auth(client):
    response = client.post("/api/applications", json={"company": "TCS", "role": "Analyst"})
    assert response.status_code == 401


def test_create_application_success(client, auth_headers):
    response = client.post(
        "/api/applications",
        json={"company": "TCS", "role": "Ninja", "status": "Applied", "location": "Chittapur"},
        headers=auth_headers,
    )
    body = response.get_json()
    assert response.status_code == 201
    assert body["company"] == "TCS"
    assert body["status"] == "Applied"


def test_create_application_invalid_status_rejected(client, auth_headers):
    response = client.post(
        "/api/applications",
        json={"company": "TCS", "role": "Ninja", "status": "NotARealStatus"},
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_create_application_missing_required_field(client, auth_headers):
    response = client.post(
        "/api/applications", json={"role": "Ninja"}, headers=auth_headers
    )
    assert response.status_code == 422


def test_list_applications_returns_only_own(client, auth_headers, sample_application):
    other_user = client.post(
        "/api/auth/register",
        json={"name": "Other", "email": "other@example.com", "password": "OtherPass123"},
    ).get_json()
    other_headers = {"Authorization": f"Bearer {other_user['access_token']}"}
    client.post(
        "/api/applications",
        json={"company": "Infosys", "role": "SysEng"},
        headers=other_headers,
    )

    response = client.get("/api/applications", headers=auth_headers)
    body = response.get_json()
    assert response.status_code == 200
    assert body["total"] == 1
    assert body["items"][0]["company"] == "Amazon"


def test_get_single_application(client, auth_headers, sample_application):
    app_id = sample_application["id"]
    response = client.get(f"/api/applications/{app_id}", headers=auth_headers)
    assert response.status_code == 200
    assert "history" in response.get_json()


def test_get_application_not_found(client, auth_headers):
    response = client.get("/api/applications/does-not-exist", headers=auth_headers)
    assert response.status_code == 404


def test_cannot_access_other_users_application(client, auth_headers, sample_application):
    other_user = client.post(
        "/api/auth/register",
        json={"name": "Other", "email": "other2@example.com", "password": "OtherPass123"},
    ).get_json()
    other_headers = {"Authorization": f"Bearer {other_user['access_token']}"}

    response = client.get(f"/api/applications/{sample_application['id']}", headers=other_headers)
    assert response.status_code == 404


def test_update_application_status_records_history(client, auth_headers, sample_application):
    app_id = sample_application["id"]
    response = client.put(
        f"/api/applications/{app_id}", json={"status": "Interview"}, headers=auth_headers
    )
    assert response.status_code == 200
    assert response.get_json()["status"] == "Interview"

    detail = client.get(f"/api/applications/{app_id}", headers=auth_headers).get_json()
    statuses = [h["to_status"] for h in detail["history"]]
    assert statuses == ["Applied", "Interview"]


def test_update_application_invalid_status(client, auth_headers, sample_application):
    app_id = sample_application["id"]
    response = client.put(
        f"/api/applications/{app_id}", json={"status": "Ghosted"}, headers=auth_headers
    )
    assert response.status_code == 422


def test_delete_application(client, auth_headers, sample_application):
    app_id = sample_application["id"]
    response = client.delete(f"/api/applications/{app_id}", headers=auth_headers)
    assert response.status_code == 204

    follow_up = client.get(f"/api/applications/{app_id}", headers=auth_headers)
    assert follow_up.status_code == 404


def test_filter_by_status(client, auth_headers, sample_application):
    client.post(
        "/api/applications",
        json={"company": "Wipro", "role": "Trainee", "status": "Rejected"},
        headers=auth_headers,
    )
    response = client.get("/api/applications?status=Rejected", headers=auth_headers)
    body = response.get_json()
    assert body["total"] == 1
    assert body["items"][0]["company"] == "Wipro"


def test_search_by_company_or_role(client, auth_headers, sample_application):
    response = client.get("/api/applications?q=amaz", headers=auth_headers)
    body = response.get_json()
    assert body["total"] == 1
    assert body["items"][0]["company"] == "Amazon"


def test_pagination(client, auth_headers):
    for i in range(15):
        client.post(
            "/api/applications",
            json={"company": f"Company{i}", "role": "Engineer"},
            headers=auth_headers,
        )
    response = client.get("/api/applications?per_page=10&page=2", headers=auth_headers)
    body = response.get_json()
    assert body["page"] == 2
    assert len(body["items"]) == 5
    assert body["total"] == 15


def test_analytics_summary(client, auth_headers, sample_application):
    response = client.get("/api/applications/analytics/summary", headers=auth_headers)
    body = response.get_json()
    assert response.status_code == 200
    assert body["total_applications"] == 1
    assert body["by_status"]["Applied"] == 1


def test_csv_export(client, auth_headers, sample_application):
    response = client.get("/api/applications/export/csv", headers=auth_headers)
    assert response.status_code == 200
    assert response.mimetype == "text/csv"
    assert b"Amazon" in response.data
