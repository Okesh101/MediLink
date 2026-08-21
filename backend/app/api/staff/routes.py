# app/api/staff/routes.py

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging

from app import db, limiter
from app.models.Hospital import Hospital
from app.models.Staff import Staff
from app.models.Role import Role
from app.models.Patient import Patient
from app.models.AIConversation import AIConversation
from app.models.SystemModels import TimelineEvent
from app.services.scheduler.meddyscheduler import schedule_patient_discharge
from app.utils.decorators import permissions_required, actor_types_required
from app.utils.helpers import as_uuid
from app.utils.types import Sex

staff_bp = Blueprint("staff", __name__)
logger = logging.getLogger(__name__)


@staff_bp.route("/doctor", methods=["POST"])
@limiter.limit('10 per minute')
@jwt_required()
@actor_types_required("hospital_admin")
@permissions_required("hospital:manage_staff")
def onboard_doctor_endpoint():
    current_hospital_id = as_uuid(get_jwt_identity())
    data = request.get_json() or {}

    required_fields = ['name', 'email', 'phone', 'nin', 'sex', 'password']
    if not all(data.get(field) for field in required_fields):
        return jsonify({"status": "ERROR", "message": "Missing required fields", "code": 400}), 400

    phone = str(data.get('phone', '')).strip()
    if not phone.isdigit() or len(phone) != 11:
        return jsonify({"status": "ERROR", "message": "Phone number must be 11 digits", "code": 400}), 400

    nin = str(data.get('nin', '')).strip()
    if not nin.isdigit() or len(nin) != 11:
        return jsonify({"status": "ERROR", "message": "NIN must be 11 digits", "code": 400}), 400

    sex = str(data.get('sex', '')).strip().lower()
    real_sex = Sex.FEMALE.value if sex in (
        'f', 'female') else Sex.MALE.value if sex in ('m', 'male') else None
    if not real_sex:
        return jsonify({"status": "ERROR", "message": "Sex must be male or female.", "code": 400}), 400

    if db.session.execute(db.select(Staff).filter_by(email=data['email'])).scalar_one_or_none():
        return jsonify({"status": "ERROR", "message": "Email already registered", "code": 409}), 409

    hospital = db.session.get(Hospital, current_hospital_id)
    if not hospital:
        return jsonify({"status": "ERROR", "code": 404, "message": "Hospital not found"}), 404

    new_staff = Staff(
        hospital_id=current_hospital_id,
        name=data['name'],
        specialty=data.get('specialty'),  # <-- ACCEPTS DOCTOR SPECIALTY
        email=data['email'],
        phone=phone,
        sex=real_sex,
        nin=nin,
    )
    new_staff.set_password(data['password'])

    doctor_role = db.session.execute(
        db.select(Role).filter_by(name="Doctor")
    ).scalar_one_or_none()

    if not doctor_role:
        return jsonify({"status": "ERROR", "code": 500, "message": "Doctor role missing."}), 500

    try:
        db.session.add(new_staff)
        db.session.flush()

        new_staff.assign_role(doctor_role)
        db.session.commit()

        created = db.session.get(Staff, new_staff.id)
        return jsonify({
            "status": "CREATED",
            "message": "Doctor registered successfully!",
            "data": created.to_dict(),
            "code": 201
        }), 201
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({"status": "ERROR", "message": "Database conflict occurred.", "code": 409}), 409


@staff_bp.route("", methods=["GET"])
@limiter.limit('20 per minute')
@jwt_required()
@actor_types_required("hospital_admin")
@permissions_required("hospital:view_staff")
def list_staff_endpoint():
    current_hospital_id = as_uuid(get_jwt_identity())
    staff_members = db.session.scalars(
        db.select(Staff).where(Staff.hospital_id ==
                               current_hospital_id).order_by(Staff.created_at.desc())
    ).all()

    return jsonify({
        "status": "SUCCESS",
        "code": 200,
        "count": len(staff_members),
        "data": [member.to_dict() for member in staff_members]
    }), 200


@staff_bp.route("/<staff_id>", methods=["GET"])
@limiter.limit('20 per minute')
@jwt_required()
@actor_types_required("hospital_admin")
@permissions_required("hospital:view_staff")
def get_staff_endpoint(staff_id):
    current_hospital_id = as_uuid(get_jwt_identity())
    parsed_staff_id = as_uuid(staff_id)
    if not parsed_staff_id:
        return jsonify({"status": "ERROR", "code": 400, "message": "Invalid staff ID."}), 400

    staff = db.session.get(Staff, parsed_staff_id)
    if not staff or staff.hospital_id != current_hospital_id:
        return jsonify({"status": "ERROR", "code": 404, "message": "Staff not found."}), 404

    return jsonify({"status": "SUCCESS", "code": 200, "data": staff.to_dict()}), 200


# --- NEW DOCTOR CLINICAL FEATURES ---

@staff_bp.route("/doctor/patient-summary/<patient_public_id>", methods=["GET"])
@limiter.limit('20 per minute')
@jwt_required()
@actor_types_required("staff")
def get_patient_ai_summary(patient_public_id):
    conversation = db.session.execute(
        db.select(AIConversation)
        .filter_by(patient_public_id=patient_public_id, status='completed')
        .order_by(AIConversation.created_at.desc())
    ).scalars().first()

    if not conversation:
        return jsonify({"status": "ERROR", "code": 404, "message": "No active or completed AI summary found."}), 404

    return jsonify({
        "status": "SUCCESS",
        "code": 200,
        "data": {
            "patient_public_id": patient_public_id,
            "summary": conversation.symptom_summary,
            "date": conversation.created_at.strftime("%Y-%m-%d %H:%M")
        }
    }), 200


@staff_bp.route("/doctor/discharge", methods=["POST"])
@limiter.limit('10 per minute')
@jwt_required()
@actor_types_required("staff")
def discharge_patient_endpoint():
    doctor_id = as_uuid(get_jwt_identity())
    doctor = db.session.get(Staff, doctor_id)
    data = request.get_json() or {}

    patient_public_id = data.get("patient_public_id")
    discharge_notes = data.get(
        "discharge_notes", "Patient discharged in stable condition.")

    if not patient_public_id:
        return jsonify({"status": "ERROR", "code": 400, "message": "patient_public_id is required."}), 400

    patient = db.session.execute(
        db.select(Patient).filter_by(public_id=patient_public_id)
    ).scalar_one_or_none()

    if not patient:
        return jsonify({"status": "ERROR", "code": 404, "message": "Patient not found."}), 404

    hospital_name = doctor.hospital.name if doctor and doctor.hospital else "Hospital"

    # Log timeline entry
    timeline_entry = TimelineEvent(
        patient_public_id=patient_public_id,
        title="Discharged from Hospital",
        description=f"Discharged from {hospital_name}. Notes: {discharge_notes}",
        event_type="DISCHARGE"
    )
    db.session.add(timeline_entry)
    db.session.commit()

    # Schedule follow-up check-in in 2 minutes
    schedule_patient_discharge(
        patient_public_id, hospital_name, delay_minutes=2)

    return jsonify({
        "status": "SUCCESS",
        "code": 200,
        "message": "Patient discharged successfully. Automated follow-up check-in scheduled for 2 minutes."
    }), 200
