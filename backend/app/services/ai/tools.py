# app/services/ai/tools.py

from app import db
from app.models.Hospital import Hospital
from app.models.Staff import Staff
from app.models.MedicalRecord import MedicalRecord
from app.models.Patient import Patient

GROQ_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_hospitals",
            "description": "Find verified hospitals by name, area, address, or location.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location_query": {
                        "type": "string",
                        "description": "City, area, or keyword e.g. 'Ikeja', 'Lekki'"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_patient_medical_profile",
            "description": "Retrieve clinical profile data like allergies, blood group, and genotype for safety context.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_public_id": {"type": "string"}
                },
                "required": ["patient_public_id"]
            }
        }
    }
]


def execute_search_hospitals(location_query: str = None) -> list:
    query = db.select(Hospital).filter_by(is_verified=True)
    if location_query:
        query = query.filter(
            db.or_(
                Hospital.address.ilike(f"%{location_query}%"),
                Hospital.name.ilike(f"%{location_query}%")
            )
        )
    hospitals = db.session.execute(query).scalars().all()
    return [
        {
            "name": h.name,
            "address": h.address,
            "phone": h.phone,
            "email": h.email
        }
        for h in hospitals
    ]


def execute_get_patient_medical_profile(patient_public_id: str) -> dict:
    patient = db.session.execute(
        db.select(Patient).filter_by(public_id=patient_public_id)
    ).scalar_one_or_none()

    if not patient:
        return {"error": "Patient not found."}

    return {
        "allergies": patient.allergies or "None reported",
        "blood_group": patient.blood_group or "Unknown",
        "genotype": patient.genotype or "Unknown"
    }


def handle_tool_call(tool_name: str, arguments: dict):
    if tool_name == "search_hospitals":
        return execute_search_hospitals(**arguments)
    elif tool_name == "get_patient_medical_profile":
        return execute_get_patient_medical_profile(**arguments)
    return {"error": "Tool not found."}
