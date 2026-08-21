# app/api/patient/routes.py

import os
from flask import Blueprint, jsonify, request, Response
from werkzeug.utils import secure_filename
from sqlalchemy import desc
import logging

from app import db, limiter
from app.models.Patient import Patient
from app.models.MedicalRecord import MedicalRecord
from app.models.AIConversation import AIConversation
from app.models.SystemModels import TimelineEvent
from app.services.ai.meddy import handle_patient_chat_stream
from app.services.ai.audio import transcribe_voice_note
from app.services.ai.summary import generate_conversation_summary
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
    current_patient_id = as_uuid(get_jwt_identity())
    patient = db.session.get(Patient, current_patient_id)

    if not patient:
        return jsonify({"status": "ERROR", "code": 404, "message": "Patient not found."}), 404

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
        return jsonify({"status": "ERROR", "code": 404, "message": "Patient not found."}), 404

    parsed_record_id = as_uuid(record_id)
    if parsed_record_id is None:
        return jsonify({"status": "ERROR", "code": 400, "message": "Invalid record ID."}), 400

    record = db.session.get(MedicalRecord, parsed_record_id)
    if not record or record.patient_public_id != patient.public_id:
        return jsonify({"status": "ERROR", "code": 404, "message": "Medical record not found."}), 404

    return jsonify({
        "status": "SUCCESS",
        "message": "Medical record retrieved successfully.",
        "data": record.to_dict(),
        "code": 200
    }), 200


# --- NEW AI & TIMELINE ENDPOINTS ---

@patient_bp.route("/ai/chat", methods=["POST"])
@limiter.limit('30 per minute')
@jwt_required()
@actor_types_required("patient")
def ai_chat_endpoint():
    current_patient_id = as_uuid(get_jwt_identity())
    patient = db.session.get(Patient, current_patient_id)

    if not patient:
        return jsonify({"status": "ERROR", "code": 404, "message": "Patient not found."}), 404

    data = request.get_json() or {}
    message = data.get("message")

    if not message:
        return jsonify({"status": "ERROR", "code": 400, "message": "Message content is required."}), 400

    return Response(
        handle_patient_chat_stream(patient.public_id, message),
        mimetype='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'}
    )


@patient_bp.route("/ai/voice-chat", methods=["POST"])
@limiter.limit('10 per minute')
@jwt_required()
@actor_types_required("patient")
def ai_voice_chat_endpoint():
    if 'audio' not in request.files:
        return jsonify({"status": "ERROR", "code": 400, "message": "Audio file is required."}), 400

    audio_file = request.files['audio']
    filename = secure_filename(audio_file.filename)
    temp_path = os.path.join("/tmp", filename)
    audio_file.save(temp_path)

    try:
        transcription = transcribe_voice_note(temp_path)
    except Exception as e:
        logger.error(f"Transcription error: {str(e)}", exc_info=True)
        return jsonify({"status": "ERROR", "code": 500, "message": "Failed to transcribe audio."}), 500
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    return jsonify({
        "status": "SUCCESS",
        "code": 200,
        "data": {"transcription": transcription}
    }), 200


@patient_bp.route("/ai/summary", methods=["POST"])
@limiter.limit('10 per minute')
@jwt_required()
@actor_types_required("patient")
def generate_summary_endpoint():
    data = request.get_json() or {}
    conversation_id = data.get("conversation_id")

    if not conversation_id:
        return jsonify({"status": "ERROR", "code": 400, "message": "conversation_id is required."}), 400

    summary = generate_conversation_summary(conversation_id)
    return jsonify({
        "status": "SUCCESS",
        "code": 200,
        "data": {"conversation_id": conversation_id, "summary": summary}
    }), 200


@patient_bp.route("/timeline", methods=["GET"])
@limiter.limit('30 per minute')
@jwt_required()
@actor_types_required("patient")
def view_timeline_endpoint():
    current_patient_id = as_uuid(get_jwt_identity())
    patient = db.session.get(Patient, current_patient_id)

    if not patient:
        return jsonify({"status": "ERROR", "code": 404, "message": "Patient not found."}), 404

    events = db.session.scalars(
        db.select(TimelineEvent)
        .where(TimelineEvent.patient_public_id == patient.public_id)
        .order_by(desc(TimelineEvent.created_at))
    ).all()

    return jsonify({
        "status": "SUCCESS",
        "code": 200,
        "count": len(events),
        "data": [event.to_dict() for event in events]
    }), 200


@patient_bp.route("/profile/medical", methods=["PUT"])
@limiter.limit('10 per minute')
@jwt_required()
@actor_types_required("patient")
def update_medical_profile():
    current_patient_id = as_uuid(get_jwt_identity())
    patient = db.session.get(Patient, current_patient_id)

    if not patient:
        return jsonify({"status": "ERROR", "code": 404, "message": "Patient not found."}), 404

    data = request.get_json() or {}
    patient.allergies = data.get("allergies", patient.allergies)
    patient.blood_group = data.get("blood_group", patient.blood_group)
    patient.genotype = data.get("genotype", patient.genotype)

    db.session.commit()

    return jsonify({
        "status": "SUCCESS",
        "code": 200,
        "message": "Medical profile updated.",
        "data": patient.to_dict()
    }), 200
