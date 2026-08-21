# tests/test_records.py

from tests.conftest import (
    auth_header,
    bootstrap_actors,
    sample_document,
)


def _grant_access(client, actors):
    public_id = actors["patient"]["public_id"]
    requested = client.post(
        "/api/v1/access/request",
        json={"patient_public_id": public_id, "reason": "Consultation"},
        headers=auth_header(actors["staff_token"]),
    )
    request_id = requested.get_json()["data"]["id"]
    client.post(
        f"/api/v1/access/requests/{request_id}/review",
        json={"status": "Approved"},
        headers=auth_header(actors["patient_token"]),
    )
    return public_id


def test_lookup_patient_without_grant(client):
    actors = bootstrap_actors(client)
    public_id = actors["patient"]["public_id"]

    response = client.get(
        f"/api/v1/records/patient/{public_id}/lookup",
        headers=auth_header(actors["staff_token"]),
    )
    data = response.get_json()
    assert response.status_code == 200
    assert data["data"]["firstname"] == "Ada"
    assert data["data"]["has_active_grant"] is False
    assert "diagnosis" not in data["data"]


def test_doctor_is_blocked_from_records_without_grant(client):
    actors = bootstrap_actors(client)
    public_id = actors["patient"]["public_id"]

    response = client.get(
        f"/api/v1/records/patient/{public_id}",
        headers=auth_header(actors["staff_token"]),
    )
    data = response.get_json()
    assert response.status_code == 403
    assert data["access_required"] is True
    assert data["has_pending_request"] is False


def test_doctor_cannot_upload_without_grant(client):
    actors = bootstrap_actors(client)
    response = client.post(
        "/api/v1/records",
        json={
            "patient_public_id": actors["patient"]["public_id"],
            "diagnosis": "Malaria",
        },
        headers=auth_header(actors["staff_token"]),
    )
    assert response.status_code == 403
    assert response.get_json()["access_required"] is True


def test_doctor_can_read_and_write_after_grant(client):
    actors = bootstrap_actors(client)
    public_id = _grant_access(client, actors)

    empty = client.get(
        f"/api/v1/records/patient/{public_id}",
        headers=auth_header(actors["staff_token"]),
    )
    assert empty.status_code == 200
    assert empty.get_json()["count"] == 0

    created = client.post(
        "/api/v1/records",
        data={
            "patient_public_id": public_id,
            "chief_complaint": "High fever and chills",
            "diagnosis": "Malaria",
            "doctor_notes": "Started artemether-lumefantrine",
            "document_titles": "Blood Film Result",
            "documents": sample_document("blood-film.pdf"),
        },
        headers=auth_header(actors["staff_token"]),
    )
    created_data = created.get_json()
    assert created.status_code == 201
    assert created_data["data"]["diagnosis"] == "Malaria"
    assert created_data["data"]["doctor_id"] == actors["doctor"]["id"]
    assert created_data["data"]["documents"][0]["title"] == "Blood Film Result"
    record_id = created_data["data"]["id"]

    history = client.get(
        f"/api/v1/records/patient/{public_id}",
        headers=auth_header(actors["staff_token"]),
    )
    assert history.status_code == 200
    assert history.get_json()["count"] == 1

    single = client.get(
        f"/api/v1/records/{record_id}",
        headers=auth_header(actors["staff_token"]),
    )
    assert single.status_code == 200
    assert single.get_json()["data"]["id"] == record_id

    mine = client.get(
        "/api/v1/records/mine",
        headers=auth_header(actors["staff_token"]),
    )
    assert mine.status_code == 200
    assert mine.get_json()["count"] == 1


def test_patient_can_view_own_records(client):
    actors = bootstrap_actors(client)
    public_id = _grant_access(client, actors)
    client.post(
        "/api/v1/records",
        json={
            "patient_public_id": public_id,
            "diagnosis": "Typhoid",
            "doctor_notes": "Requested Widal test",
        },
        headers=auth_header(actors["staff_token"]),
    )

    own = client.get(
        "/api/v1/patient/records",
        headers=auth_header(actors["patient_token"]),
    )
    data = own.get_json()
    assert own.status_code == 200
    assert data["count"] == 1
    assert data["data"][0]["diagnosis"] == "Typhoid"

    record_id = data["data"][0]["id"]
    single = client.get(
        f"/api/v1/patient/records/{record_id}",
        headers=auth_header(actors["patient_token"]),
    )
    assert single.status_code == 200


def test_revoked_grant_blocks_records_again(client):
    actors = bootstrap_actors(client)
    public_id = _grant_access(client, actors)

    grants = client.get(
        "/api/v1/access/grants",
        headers=auth_header(actors["patient_token"]),
    )
    grant_id = grants.get_json()["data"][0]["id"]
    client.post(
        f"/api/v1/access/grants/{grant_id}/revoke",
        headers=auth_header(actors["patient_token"]),
    )

    blocked = client.get(
        f"/api/v1/records/patient/{public_id}",
        headers=auth_header(actors["staff_token"]),
    )
    assert blocked.status_code == 403
    assert blocked.get_json()["access_required"] is True


def test_hospital_cannot_read_medical_records(client):
    actors = bootstrap_actors(client)
    response = client.get(
        f"/api/v1/records/patient/{actors['patient']['public_id']}",
        headers=auth_header(actors["hospital_token"]),
    )
    assert response.status_code == 403


def test_create_record_requires_diagnosis(client):
    actors = bootstrap_actors(client)
    public_id = _grant_access(client, actors)
    response = client.post(
        "/api/v1/records",
        json={"patient_public_id": public_id},
        headers=auth_header(actors["staff_token"]),
    )
    assert response.status_code == 400
