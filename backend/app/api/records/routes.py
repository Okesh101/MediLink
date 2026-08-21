# app/api/records/routes.py

from flask import Blueprint, jsonify, request
from sqlalchemy import desc
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
import logging

from app import db, limiter
from app.models.Staff import Staff
from app.models.Patient import Patient
from app.models.MedicalRecord import MedicalRecord
from app.models.RecordDocuments import RecordDocuments
from app.utils.decorators import permissions_required, actor_types_required
from app.utils.helpers import as_uuid, find_patient_by_public_id, get_active_grant, get_pending_request
from app.services.cloudinary.cloudinary import upload_file_to_cloudinary

records_bp = Blueprint("records", __name__)
logger = logging.getLogger(__name__)


def _access_denied_payload(staff, patient):
    pending = get_pending_request(staff.id, patient.public_id)
    return {
        "status": "ERROR",
        "code": 403,
        "message": (
            "Access to this patient's records is not granted. "
            "Request access and wait for the patient to approve."
        ),
        "access_required": True,
        "has_pending_request": pending is not None,
        "pending_request_id": str(pending.id) if pending else None,
    }


def _staff_can_access_patient(staff, patient):
    return get_active_grant(staff.id, patient.public_id) is not None


@records_bp.route("/patient/<public_id>/lookup", methods=["GET"])
@limiter.limit("20 per minute")
@jwt_required()
@actor_types_required("staff")
@permissions_required("patient:lookup")
def lookup_patient_endpoint(public_id):
    """Confirm a patient identity from their public ID without exposing records."""
    patient = find_patient_by_public_id(public_id)
    if not patient:
        return jsonify({
            "status": "ERROR",
            "message": "Patient not found.",
            "code": 404
        }), 404

    staff = db.session.get(Staff, as_uuid(get_jwt_identity()))
    grant = get_active_grant(staff.id, patient.public_id) if staff else None
    pending = get_pending_request(staff.id, patient.public_id) if staff else None

    return jsonify({
        "status": "SUCCESS",
        "message": "Patient identity retrieved successfully.",
        "data": {
            "public_id": patient.public_id,
            "firstname": patient.firstname,
            "lastname": patient.lastname,
            "sex": patient.sex,
            "dob": patient.dob.strftime("%Y-%m-%d") if patient.dob else None,
            "has_active_grant": grant is not None,
            "has_pending_request": pending is not None,
        },
        "code": 200
    }), 200


@records_bp.route("/patient/<public_id>", methods=["GET"])
@limiter.limit("20 per minute")
@jwt_required()
@actor_types_required("staff")
@permissions_required("medical_record:read")
def view_patient_records_endpoint(public_id):
    """Doctor views a patient's full history after the patient grants access."""
    current_staff_id = as_uuid(get_jwt_identity())
    staff = db.session.get(Staff, current_staff_id)
    if not staff:
        return jsonify({
            "status": "ERROR",
            "message": "Staff record not found.",
            "code": 404
        }), 404

    patient = find_patient_by_public_id(public_id)
    if not patient:
        return jsonify({
            "status": "ERROR",
            "message": "Patient not found.",
            "code": 404
        }), 404

    if not _staff_can_access_patient(staff, patient):
        return jsonify(_access_denied_payload(staff, patient)), 403

    records = db.session.scalars(
        db.select(MedicalRecord)
        .where(MedicalRecord.patient_public_id == patient.public_id)
        .order_by(desc(MedicalRecord.created_at))
    ).all()

    return jsonify({
        "status": "SUCCESS",
        "message": "Patient medical records retrieved successfully.",
        "count": len(records),
        "data": [record.to_dict() for record in records],
        "code": 200
    }), 200


@records_bp.route("", methods=["POST"])
@limiter.limit("15 per minute")
@jwt_required()
@actor_types_required("staff")
@permissions_required("medical_record:write")
def create_patient_record_endpoint():
    """Doctor uploads a new encounter (diagnosis + named documents) for a patient."""
    current_staff_id = as_uuid(get_jwt_identity())
    staff = db.session.get(Staff, current_staff_id)
    if not staff:
        return jsonify({
            "status": "ERROR",
            "message": "Staff record not found.",
            "code": 404
        }), 404

    payload = request.form if request.form else (request.get_json(silent=True) or {})
    patient_public_id = payload.get("patient_public_id")
    diagnosis = (payload.get("diagnosis") or "").strip()

    if not patient_public_id or not diagnosis:
        logger.warning("Attempt to upload medical record with missing fields.")
        return jsonify({
            "status": "ERROR",
            "message": "Missing required fields: patient_public_id and diagnosis.",
            "code": 400
        }), 400

    patient = find_patient_by_public_id(patient_public_id)
    if not patient:
        return jsonify({
            "status": "ERROR",
            "message": "Patient not found.",
            "code": 404
        }), 404

    if not _staff_can_access_patient(staff, patient):
        return jsonify(_access_denied_payload(staff, patient)), 403

    files = request.files.getlist("documents") if request.files else []
    titles = request.form.getlist("document_titles") if request.form else []

    try:
        new_record = MedicalRecord(
            hospital_id=staff.hospital_id,
            doctor_id=staff.id,
            patient_public_id=patient.public_id,
            chief_complaint=(payload.get("chief_complaint") or "").strip() or None,
            diagnosis=diagnosis,
            doctor_notes=(payload.get("doctor_notes") or "").strip() or None,
        )
        db.session.add(new_record)
        db.session.flush()

        uploaded_docs = []
        for index, file in enumerate(files):
            if not file or not file.filename:
                continue

            custom_title = (
                titles[index].strip()
                if index < len(titles) and titles[index].strip()
                else file.filename
            )

            doc_url = upload_file_to_cloudinary(
                file, folder="medical_records")
            if not doc_url:
                db.session.rollback()
                logger.error(
                    "Cloudinary upload failed for document: %s", custom_title)
                return jsonify({
                    "status": "ERROR",
                    "message": f"Failed to upload document: {custom_title}",
                    "code": 500
                }), 500

            uploaded_docs.append(RecordDocuments(
                record_id=new_record.id,
                title=custom_title,
                doc_url=doc_url,
            ))

        if uploaded_docs:
            db.session.add_all(uploaded_docs)

        db.session.commit()

        created = db.session.get(MedicalRecord, new_record.id)
        return jsonify({
            "status": "CREATED",
            "message": "Medical record created successfully.",
            "data": created.to_dict(),
            "code": 201
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error("Medical record creation crash: %s", str(e), exc_info=True)
        return jsonify({
            "status": "ERROR",
            "message": "An internal system error occurred.",
            "code": 500
        }), 500


@records_bp.route("/mine", methods=["GET"])
@limiter.limit("20 per minute")
@jwt_required()
@actor_types_required("staff")
@permissions_required("medical_record:read")
def view_own_authored_records_endpoint():
    current_staff_id = as_uuid(get_jwt_identity())
    staff = db.session.get(Staff, current_staff_id)
    if not staff:
        return jsonify({
            "status": "ERROR",
            "message": "Staff record not found.",
            "code": 404
        }), 404

    records = db.session.scalars(
        db.select(MedicalRecord)
        .where(MedicalRecord.doctor_id == staff.id)
        .order_by(desc(MedicalRecord.created_at))
    ).all()

    return jsonify({
        "status": "SUCCESS",
        "message": "Authored medical records retrieved successfully.",
        "count": len(records),
        "data": [record.to_dict() for record in records],
        "code": 200
    }), 200


@records_bp.route("/<record_id>", methods=["GET"])
@limiter.limit("20 per minute")
@jwt_required()
@actor_types_required("staff", "patient")
@permissions_required("medical_record:read", "medical_record:view_own")
def view_single_record_endpoint(record_id):
    parsed_id = as_uuid(record_id)
    if parsed_id is None:
        return jsonify({
            "status": "ERROR",
            "message": "Invalid record ID.",
            "code": 400
        }), 400

    record = db.session.get(MedicalRecord, parsed_id)
    if not record:
        return jsonify({
            "status": "ERROR",
            "message": "Medical record not found.",
            "code": 404
        }), 404

    claims = get_jwt()
    actor_type = claims.get("actor_type")
    actor_id = as_uuid(get_jwt_identity())

    if actor_type == "patient":
        patient = db.session.get(Patient, actor_id)
        if not patient or record.patient_public_id != patient.public_id:
            return jsonify({
                "status": "ERROR",
                "message": "Medical record not found.",
                "code": 404
            }), 404
    else:
        staff = db.session.get(Staff, actor_id)
        if not staff:
            return jsonify({
                "status": "ERROR",
                "message": "Staff record not found.",
                "code": 404
            }), 404

        patient = find_patient_by_public_id(record.patient_public_id)
        if not patient:
            return jsonify({
                "status": "ERROR",
                "message": "Medical record not found.",
                "code": 404
            }), 404
        if not _staff_can_access_patient(staff, patient):
            return jsonify(_access_denied_payload(staff, patient)), 403

    return jsonify({
        "status": "SUCCESS",
        "message": "Medical record retrieved successfully.",
        "data": record.to_dict(),
        "code": 200
    }), 200
