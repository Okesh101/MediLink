# app/api/chat/routes.py

import logging
from flask import Blueprint, request, Response
from app.services.ai.meddy import handle_patient_chat_stream

chat_bp = Blueprint('chat', __name__)
logger = logging(__name__)


@chat_bp.route('/api/v1/ai/chat', methods=['POST'])
def ai_chat():
    data = request.json or {}
    patient_public_id = data.get("patient_public_id")
    message = data.get("message")

    if not patient_public_id or not message:
        logger.warn("Patient public ID and message missing")
        return {"error": "patient_public_id and message are required."}, 400

    return Response(
        handle_patient_chat_stream(patient_public_id, message),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'  # Prevents proxy/Nginx buffering on live stream
        }
    )
