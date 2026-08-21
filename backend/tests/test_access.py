# tests/test_access.py

from tests.conftest import auth_header, bootstrap_actors


def test_doctor_request_and_patient_approve(client):
    actors = bootstrap_actors(client)
    public_id = actors["patient"]["public_id"]

    requested = client.post(
        "/api/v1/access/request",
        json={"patient_public_id": public_id, "reason": "Walk-in consultation"},
        headers=auth_header(actors["staff_token"]),
    )
    request_data = requested.get_json()
    assert requested.status_code == 201
    assert request_data["data"]["status"] == "Pending"
    request_id = request_data["data"]["id"]

    pending_list = client.get(
        "/api/v1/access/requests?status=Pending",
        headers=auth_header(actors["patient_token"]),
    )
    assert pending_list.status_code == 200
    assert pending_list.get_json()["count"] == 1

    reviewed = client.post(
        f"/api/v1/access/requests/{request_id}/review",
        json={"status": "Approved"},
        headers=auth_header(actors["patient_token"]),
    )
    review_data = reviewed.get_json()
    assert reviewed.status_code == 200
    assert review_data["data"]["request"]["status"] == "Approved"
    assert review_data["data"]["grant"]["status"] == "Granted"

    grants = client.get(
        "/api/v1/access/grants",
        headers=auth_header(actors["staff_token"]),
    )
    assert grants.status_code == 200
    assert grants.get_json()["count"] == 1


def test_duplicate_pending_request_is_rejected(client):
    actors = bootstrap_actors(client)
    public_id = actors["patient"]["public_id"]
    headers = auth_header(actors["staff_token"])

    first = client.post(
        "/api/v1/access/request",
        json={"patient_public_id": public_id},
        headers=headers,
    )
    assert first.status_code == 201

    second = client.post(
        "/api/v1/access/request",
        json={"patient_public_id": public_id},
        headers=headers,
    )
    assert second.status_code == 409


def test_patient_can_deny_request(client):
    actors = bootstrap_actors(client)
    public_id = actors["patient"]["public_id"]

    requested = client.post(
        "/api/v1/access/request",
        json={"patient_public_id": public_id},
        headers=auth_header(actors["staff_token"]),
    )
    request_id = requested.get_json()["data"]["id"]

    denied = client.post(
        f"/api/v1/access/requests/{request_id}/review",
        json={"status": "Denied"},
        headers=auth_header(actors["patient_token"]),
    )
    data = denied.get_json()
    assert denied.status_code == 200
    assert data["data"]["request"]["status"] == "Denied"
    assert data["data"]["grant"] is None


def test_patient_can_revoke_grant(client):
    actors = bootstrap_actors(client)
    public_id = actors["patient"]["public_id"]

    requested = client.post(
        "/api/v1/access/request",
        json={"patient_public_id": public_id},
        headers=auth_header(actors["staff_token"]),
    )
    request_id = requested.get_json()["data"]["id"]
    reviewed = client.post(
        f"/api/v1/access/requests/{request_id}/review",
        json={"status": "Approved"},
        headers=auth_header(actors["patient_token"]),
    )
    grant_id = reviewed.get_json()["data"]["grant"]["id"]

    revoked = client.post(
        f"/api/v1/access/grants/{grant_id}/revoke",
        headers=auth_header(actors["patient_token"]),
    )
    assert revoked.status_code == 200
    assert revoked.get_json()["data"]["status"] == "Revoked"


def test_doctor_cannot_review_access_request(client):
    actors = bootstrap_actors(client)
    public_id = actors["patient"]["public_id"]
    requested = client.post(
        "/api/v1/access/request",
        json={"patient_public_id": public_id},
        headers=auth_header(actors["staff_token"]),
    )
    request_id = requested.get_json()["data"]["id"]

    response = client.post(
        f"/api/v1/access/requests/{request_id}/review",
        json={"status": "Approved"},
        headers=auth_header(actors["staff_token"]),
    )
    assert response.status_code == 403


def test_hospital_cannot_request_access(client):
    actors = bootstrap_actors(client)
    response = client.post(
        "/api/v1/access/request",
        json={"patient_public_id": actors["patient"]["public_id"]},
        headers=auth_header(actors["hospital_token"]),
    )
    assert response.status_code == 403


def test_request_unknown_patient_returns_404(client):
    actors = bootstrap_actors(client)
    response = client.post(
        "/api/v1/access/request",
        json={"patient_public_id": "AAA-BBB-CCCC"},
        headers=auth_header(actors["staff_token"]),
    )
    assert response.status_code == 404
