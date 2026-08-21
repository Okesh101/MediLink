# tests/test_staff.py

from tests.conftest import (
    auth_header,
    register_hospital,
    login_hospital,
    create_doctor,
    login_staff,
    register_patient,
    login_patient,
)


def test_hospital_creates_and_lists_doctor(client):
    register_hospital(client)
    hospital_token = login_hospital(client).get_json()["access_token"]

    created = create_doctor(client, hospital_token)
    data = created.get_json()
    assert created.status_code == 201
    assert data["data"]["email"] == "chidi@lgh.example.com"
    assert "Doctor" in data["data"]["roles"]

    listed = client.get("/api/v1/staff", headers=auth_header(hospital_token))
    listed_data = listed.get_json()
    assert listed.status_code == 200
    assert listed_data["count"] == 1
    assert listed_data["data"][0]["name"] == "Dr. Chidi Nwosu"

    staff_id = data["data"]["id"]
    fetched = client.get(
        f"/api/v1/staff/{staff_id}",
        headers=auth_header(hospital_token),
    )
    assert fetched.status_code == 200
    assert fetched.get_json()["data"]["id"] == staff_id


def test_create_doctor_requires_password(client):
    register_hospital(client)
    hospital_token = login_hospital(client).get_json()["access_token"]

    response = client.post(
        "/api/v1/staff/doctor",
        json={
            "name": "Dr. Chidi Nwosu",
            "email": "chidi@lgh.example.com",
            "phone": "08033333333",
            "nin": "22222222222",
            "sex": "male",
        },
        headers=auth_header(hospital_token),
    )
    assert response.status_code == 400


def test_patient_cannot_create_doctor(client):
    register_patient(client)
    patient_token = login_patient(client).get_json()["access_token"]

    response = create_doctor(client, patient_token)
    assert response.status_code == 403


def test_staff_cannot_create_doctor(client):
    register_hospital(client)
    hospital_token = login_hospital(client).get_json()["access_token"]
    create_doctor(client, hospital_token)
    staff_token = login_staff(client).get_json()["access_token"]

    response = create_doctor(
        client,
        staff_token,
        email="other@lgh.example.com",
        phone="08055555555",
        nin="33333333333",
    )
    assert response.status_code == 403


def test_created_doctor_can_login_and_view_profile(client):
    register_hospital(client)
    hospital_token = login_hospital(client).get_json()["access_token"]
    create_doctor(client, hospital_token)

    login = login_staff(client)
    assert login.status_code == 200

    me = client.get(
        "/api/v1/auth/staff/me",
        headers=auth_header(login.get_json()["access_token"]),
    )
    assert me.status_code == 200
    assert me.get_json()["data"]["email"] == "chidi@lgh.example.com"
