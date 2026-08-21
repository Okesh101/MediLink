# tests/conftest.py

import pytest
from io import BytesIO

from app import create_app, db, seed_system_permissions_and_roles
from app.config.config import TestingConfig


@pytest.fixture
def app():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        seed_system_permissions_and_roles()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def mock_cloudinary(monkeypatch):
    def _fake_upload(file_storage, folder="medical_records"):
        filename = getattr(file_storage, "filename", None) or "document.bin"
        return f"https://cdn.example.com/{folder}/{filename}"

    monkeypatch.setattr(
        "app.api.records.routes.upload_file_to_cloudinary",
        _fake_upload,
    )


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def register_patient(client, **overrides):
    payload = {
        "firstname": "Ada",
        "lastname": "Okafor",
        "sex": "female",
        "phone": "08011111111",
        "dob": "1995-04-23",
        "nin": "11111111111",
        "password": "PatientPass1",
        "email": "ada@example.com",
    }
    payload.update(overrides)
    return client.post("/api/v1/auth/patient/register", json=payload)


def login_patient(client, phone="08011111111", password="PatientPass1"):
    return client.post("/api/v1/auth/patient/login", json={
        "phone": phone,
        "password": password,
    })


def register_hospital(client, **overrides):
    payload = {
        "reg_no": "HM/2024/001",
        "name": "Lagos General Hospital",
        "email": "admin@lgh.example.com",
        "phone": "08022222222",
        "address": "1 Broad Street, Lagos",
        "password": "HospitalPass1",
    }
    payload.update(overrides)
    return client.post("/api/v1/auth/hospital/register", json=payload)


def login_hospital(client, email="admin@lgh.example.com", password="HospitalPass1"):
    return client.post("/api/v1/auth/hospital/login", json={
        "email": email,
        "password": password,
    })


def create_doctor(client, hospital_token, **overrides):
    payload = {
        "name": "Dr. Chidi Nwosu",
        "email": "chidi@lgh.example.com",
        "phone": "08033333333",
        "nin": "22222222222",
        "sex": "male",
        "password": "DoctorPass1",
    }
    payload.update(overrides)
    return client.post(
        "/api/v1/staff/doctor",
        json=payload,
        headers=auth_header(hospital_token),
    )


def login_staff(client, email="chidi@lgh.example.com", password="DoctorPass1"):
    return client.post("/api/v1/auth/staff/login", json={
        "email": email,
        "password": password,
    })


def bootstrap_actors(client):
    """Register a patient, hospital, and doctor, then return tokens and IDs."""
    patient_res = register_patient(client)
    patient = patient_res.get_json()["data"]
    patient_login = login_patient(client).get_json()

    hospital_res = register_hospital(client)
    hospital = hospital_res.get_json()["data"]
    hospital_login = login_hospital(client).get_json()

    doctor_res = create_doctor(client, hospital_login["access_token"])
    doctor = doctor_res.get_json()["data"]
    staff_login = login_staff(client).get_json()

    return {
        "patient": patient,
        "hospital": hospital,
        "doctor": doctor,
        "patient_token": patient_login["access_token"],
        "hospital_token": hospital_login["access_token"],
        "staff_token": staff_login["access_token"],
        "patient_refresh": patient_login["refresh_token"],
        "staff_refresh": staff_login["refresh_token"],
    }


def sample_document(filename="blood-film.pdf", content=b"%PDF-1.4 test"):
    return (BytesIO(content), filename)
