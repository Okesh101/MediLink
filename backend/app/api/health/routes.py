# app/api/health/routes.py

import time
from flask import Blueprint, jsonify

app_start_time = time.time()

health_bp = Blueprint("health", __name__)

# api/v1/health
@health_bp.route("", methods=["GET"])
def health_check():
    request_start_time = time.time()

    uptime_seconds = int(time.time() - app_start_time)

    response_data = {
        "status": "SUCCESS",
        "code": 200,
        "message": "MediLink API is healthy and running.",
        "meta": {
            "uptime": f"{uptime_seconds} secs" if uptime_seconds > 1 else f"{uptime_seconds} sec",
        }
    }

    execution_time_ms = round((time.time() - request_start_time) * 1000, 2)

    response_data["meta"]["response_time"] = f"{execution_time_ms} ms"

    return jsonify(response_data)

# api/v1/health/me
@health_bp.route("/me", methods=['GET'])
def pinging_endpoint():
    return jsonify({
        "status": "OK",
        "code": 200,
        "message": "Service is running."
    })
