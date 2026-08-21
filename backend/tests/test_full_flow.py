# tests/test_full_flow.py

from tests.conftest import (
    auth_header,
    register_patient,
    login_patient,
    register_hospital,
    login_hospital,
    create_doctor,
    login_staff,
    sample_document,
)


def test_end_to_end_clinical_records_flow(client):
    """Patient register -> hospital onboard -> doctor created -> consent -> records."""

    # 1. Patient is registered and receives a public ID
    patient_res = register_patient(client)
    assert patient_res.status_code == 201
    public_id = patient_res.get_json()["data"]["public_id"]
    patient_token = login_patient(client).get_json()["access_token"]

    # 2. Hospital is onboarded with its registration number
    hospital_res = register_hospital(client)
    assert hospital_res.status_code == 201
    hospital_token = login_hospital(client).get_json()["access_token"]

    # 3. Hospital creates a staff (doctor) account
    doctor_res = create_doctor(client, hospital_token)
    assert doctor_res.status_code == 201
    staff_token = login_staff(client).get_json()["access_token"]

    # 4. Doctor looks up the walking-in patient
    lookup = client.get(
        f"/api/v1/records/patient/{public_id}/lookup",
        headers=auth_header(staff_token),
    )
    assert lookup.status_code == 200
    assert lookup.get_json()["data"]["lastname"] == "Okafor"

    # 5. Doctor is blocked from past records until consent is granted
    blocked = client.get(
        f"/api/v1/records/patient/{public_id}",
        headers=auth_header(staff_token),
    )
    assert blocked.status_code == 403
    assert blocked.get_json()["access_required"] is True

    # 6. Doctor requests access
    requested = client.post(
        "/api/v1/access/request",
        json={
            "patient_public_id": public_id.replace("-", "").lower(),
            "reason": "Patient presented with abdominal pain",
        },
        headers=auth_header(staff_token),
    )
    assert requested.status_code == 201
    request_id = requested.get_json()["data"]["id"]

    # 7. Patient sees the pending request and approves it
    inbox = client.get(
        "/api/v1/access/requests",
        headers=auth_header(patient_token),
    )
    assert inbox.status_code == 200
    assert inbox.get_json()["data"][0]["staff_name"] == "Dr. Chidi Nwosu"

    approved = client.post(
        f"/api/v1/access/requests/{request_id}/review",
        json={"status": "approved"},
        headers=auth_header(patient_token),
    )
    assert approved.status_code == 200
    assert approved.get_json()["data"]["grant"]["status"] == "Granted"

    # 8. Doctor can now read prior history (none yet) and upload this visit
    history = client.get(
        f"/api/v1/records/patient/{public_id}",
        headers=auth_header(staff_token),
    )
    assert history.status_code == 200
    assert history.get_json()["count"] == 0

    created = client.post(
        "/api/v1/records",
        data={
            "patient_public_id": public_id,
            "chief_complaint": "Abdominal pain",
            "diagnosis": "Acute appendicitis",
            "doctor_notes": "Referred for ultrasound and surgical review",
            "document_titles": ["Ultrasound Report", "FBC Result"],
            "documents": [
                sample_document("ultrasound.pdf"),
                sample_document("fbc.pdf"),
            ],
        },
        headers=auth_header(staff_token),
    )
    created_data = created.get_json()
    assert created.status_code == 201, created_data
    assert created_data["data"]["diagnosis"] == "Acute appendicitis"
    titles = {doc["title"] for doc in created_data["data"]["documents"]}
    assert titles == {"Ultrasound Report", "FBC Result"}
    assert created_data["data"]["doctor_name"] == "Dr. Chidi Nwosu"
    assert created_data["data"]["hospital_name"] == "Lagos General Hospital"

    # 9. Patient sees the new row in their lifelong record store
    own_records = client.get(
        "/api/v1/patient/records",
        headers=auth_header(patient_token),
    )
    own_data = own_records.get_json()
    assert own_records.status_code == 200
    assert own_data["count"] == 1
    assert own_data["data"][0]["diagnosis"] == "Acute appendicitis"
    assert len(own_data["data"][0]["documents"]) == 2

    # 10. A later visit at the same hospital can reuse history after a fresh grant
    grant_id = approved.get_json()["data"]["grant"]["id"]
    revoke = client.post(
        f"/api/v1/access/grants/{grant_id}/revoke",
        headers=auth_header(patient_token),
    )
    assert revoke.status_code == 200

    blocked_again = client.get(
        f"/api/v1/records/patient/{public_id}",
        headers=auth_header(staff_token),
    )
    assert blocked_again.status_code == 403
