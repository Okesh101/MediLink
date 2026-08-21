# app/services/ai/tasks.py

import threading
from flask import current_app
from app.services.ai.meddy import run_ai_risk_assessment


def trigger_ai_risk_assessment_async(loan_request_id: str):
    app = current_app._get_current_object()

    def _run():
        with app.app_context():
            run_ai_risk_assessment(loan_request_id)

    threading.Thread(target=_run, daemon=True).start()
