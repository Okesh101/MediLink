# app/api/patient/routes.py

from flask import Blueprint, jsonify
from sqlalchemy import desc
import logging

from app import db, limiter
from app.models.Patient import Patient
from app.models.MedicalRecord import MedicalRecord
from app.utils.decorators import permissions_required, actor_types_required
from app.utils.helpers import as_uuid
from flask_jwt_extended import jwt_required, get_jwt_identity

patient_bp = Blueprint("patient", __name__)
logger = logging.getLogger(__name__)


@patient_bp.route("/records", methods=["GET"])
@limiter.limit('20 per minute')
@jwt_required()
@actor_types_required("patient")
@permissions_required("medical_record:view_own")
def view_own_records_endpoint():
    """Patient views their full medical history across hospitals."""
    current_patient_id = as_uuid(get_jwt_identity())
    patient = db.session.get(Patient, current_patient_id)

    if not patient:
        logger.warning("Patient record %s not found.", current_patient_id)
        return jsonify({
            "status": "ERROR",
            "code": 404,
            "message": "Patient not found."
        }), 404

    records = db.session.scalars(
        db.select(MedicalRecord)
        .where(MedicalRecord.patient_public_id == patient.public_id)
        .order_by(desc(MedicalRecord.created_at))
    ).all()

    return jsonify({
        "status": "SUCCESS",
        "message": "Medical records retrieved successfully.",
        "count": len(records),
        "data": [record.to_dict() for record in records],
        "code": 200
    }), 200


@patient_bp.route("/records/<record_id>", methods=["GET"])
@limiter.limit('20 per minute')
@jwt_required()
@actor_types_required("patient")
@permissions_required("medical_record:view_own")
def view_own_record_endpoint(record_id):
    current_patient_id = as_uuid(get_jwt_identity())
    patient = db.session.get(Patient, current_patient_id)

    if not patient:
        return jsonify({
            "status": "ERROR",
            "code": 404,
            "message": "Patient not found."
        }), 404

    parsed_record_id = as_uuid(record_id)
    if parsed_record_id is None:
        return jsonify({
            "status": "ERROR",
            "code": 400,
            "message": "Invalid record ID."
        }), 400

    record = db.session.get(MedicalRecord, parsed_record_id)
    if not record or record.patient_public_id != patient.public_id:
        return jsonify({
            "status": "ERROR",
            "code": 404,
            "message": "Medical record not found."
        }), 404

    return jsonify({
        "status": "SUCCESS",
        "message": "Medical record retrieved successfully.",
        "data": record.to_dict(),
        "code": 200
    }), 200
