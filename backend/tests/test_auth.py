# tests/test_auth.py

from tests.conftest import (
    auth_header,
    register_patient,
    login_patient,
    register_hospital,
    login_hospital,
    create_doctor,
    login_staff,
)


def test_patient_register_returns_public_id(client):
    response = register_patient(client)
    data = response.get_json()

    assert response.status_code == 201
    assert data["status"] == "CREATED"
    assert data["data"]["public_id"]
    assert data["data"]["firstname"] == "Ada"
    assert "Patient" in data["data"]["roles"]
    assert "-" in data["data"]["public_id"]


def test_patient_register_rejects_missing_fields(client):
    response = client.post("/api/v1/auth/patient/register", json={
        "firstname": "Ada"
    })
    assert response.status_code == 400
    assert response.get_json()["status"] == "ERROR"


def test_patient_register_rejects_invalid_phone(client):
    response = register_patient(client, phone="123")
    assert response.status_code == 400


def test_patient_register_rejects_duplicate_phone(client):
    first = register_patient(client)
    assert first.status_code == 201
    second = register_patient(client, nin="33333333333", email="other@example.com")
    assert second.status_code == 409


def test_patient_login_and_me(client):
    register_patient(client)
    login = login_patient(client)
    assert login.status_code == 200
    token = login.get_json()["access_token"]

    me = client.get("/api/v1/auth/patient/me", headers=auth_header(token))
    data = me.get_json()
    assert me.status_code == 200
    assert data["data"]["phone"] == "08011111111"


def test_patient_login_rejects_bad_password(client):
    register_patient(client)
    response = login_patient(client, password="wrong")
    assert response.status_code == 401


def test_hospital_register_login_and_me(client):
    created = register_hospital(client)
    assert created.status_code == 201
    assert created.get_json()["data"]["reg_no"] == "HM/2024/001"
    assert "Hospital Admin" in created.get_json()["data"]["roles"]

    login = login_hospital(client)
    assert login.status_code == 200
    token = login.get_json()["access_token"]

    me = client.get("/api/v1/auth/hospital/me", headers=auth_header(token))
    assert me.status_code == 200
    assert me.get_json()["data"]["name"] == "Lagos General Hospital"


def test_hospital_register_rejects_duplicate_reg_no(client):
    register_hospital(client)
    duplicate = register_hospital(
        client,
        email="other@lgh.example.com",
        phone="08044444444",
    )
    assert duplicate.status_code == 409


def test_staff_cannot_use_patient_me_endpoint(client):
    register_hospital(client)
    hospital_token = login_hospital(client).get_json()["access_token"]
    create_doctor(client, hospital_token)
    staff_token = login_staff(client).get_json()["access_token"]

    response = client.get(
        "/api/v1/auth/patient/me",
        headers=auth_header(staff_token),
    )
    assert response.status_code == 403


def test_patient_logout_revokes_access_token(client):
    register_patient(client)
    login = login_patient(client).get_json()
    headers = auth_header(login["access_token"])
    headers["X-Refresh-Token"] = login["refresh_token"]

    logout = client.post("/api/v1/auth/patient/logout", headers=headers)
    assert logout.status_code == 200

    me = client.get("/api/v1/auth/patient/me", headers=auth_header(login["access_token"]))
    assert me.status_code == 401


def test_patient_refresh_issues_new_access_token(client):
    register_patient(client)
    login = login_patient(client).get_json()

    refresh = client.post(
        "/api/v1/auth/patient/refresh",
        headers=auth_header(login["refresh_token"]),
    )
    data = refresh.get_json()
    assert refresh.status_code == 200
    assert data["access_token"]

    me = client.get(
        "/api/v1/auth/patient/me",
        headers=auth_header(data["access_token"]),
    )
    assert me.status_code == 200
