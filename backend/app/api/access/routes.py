# app/api/access/routes.py

from datetime import timedelta
from flask import Blueprint, jsonify, request, current_app
from sqlalchemy import desc
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
import logging

from app import db, limiter
from app.models.Staff import Staff
from app.models.Patient import Patient
from app.models.Access import AccessGrants, Requests
from app.utils.decorators import permissions_required, actor_types_required
from app.utils.types import RequestStatus, GrantStatus, AccessScope
from app.utils.helpers import (
    as_uuid,
    find_patient_by_public_id,
    get_pending_request,
    get_active_grant,
)
from app.utils.time import lagos_now

access_bp = Blueprint("access", __name__)
logger = logging.getLogger(__name__)


def _normalize_review_status(raw_status):
    if not raw_status:
        return None
    value = str(raw_status).strip().lower()
    if value in ("approved", "approve"):
        return RequestStatus.APPROVED
    if value in ("denied", "deny", "rejected", "reject"):
        return RequestStatus.DENIED
    return None


@access_bp.route("/request", methods=["POST"])
@limiter.limit("10 per minute")
@jwt_required()
@actor_types_required("staff")
@permissions_required("access:request")
def request_access_endpoint():
    current_staff_id = as_uuid(get_jwt_identity())
    data = request.get_json() or {}

    if not data.get("patient_public_id"):
        logger.warning(
            "Attempt to request access with missing patient public ID.")
        return jsonify({
            "status": "ERROR",
            "message": "Missing required field: patient_public_id",
            "code": 400
        }), 400

    patient = find_patient_by_public_id(data["patient_public_id"])
    if not patient:
        logger.warning(
            "Patient with public ID %s not found during access request.",
            data.get("patient_public_id")
        )
        return jsonify({
            "status": "ERROR",
            "message": "Patient not found.",
            "code": 404
        }), 404

    staff = db.session.get(Staff, current_staff_id)
    if not staff:
        logger.warning(
            "Staff with ID %s not found during access request.",
            current_staff_id
        )
        return jsonify({
            "status": "ERROR",
            "message": "Staff record not found.",
            "code": 404
        }), 404

    existing_grant = get_active_grant(staff.id, patient.public_id)
    if existing_grant:
        return jsonify({
            "status": "ERROR",
            "message": "You already have active access to this patient's records.",
            "data": existing_grant.to_dict(),
            "code": 409
        }), 409

    existing_request = get_pending_request(staff.id, patient.public_id)
    if existing_request:
        return jsonify({
            "status": "ERROR",
            "message": "You already have a pending access request for this patient.",
            "data": existing_request.to_dict(),
            "code": 409
        }), 409

    try:
        new_access_request = Requests(
            patient_public_id=patient.public_id,
            staff_id=staff.id,
            hospital_id=staff.hospital_id,
            reason=(data.get("reason") or "").strip() or None,
            scope=data.get("scope") or AccessScope.VIEW_AND_CREATE_RECORDS.value,
            status=RequestStatus.PENDING.value,
        )
        db.session.add(new_access_request)
        db.session.commit()

        return jsonify({
            "status": "CREATED",
            "message": "Access request created successfully. Waiting for patient approval.",
            "data": new_access_request.to_dict(),
            "code": 201
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error("Access request crash: %s", str(e), exc_info=True)
        return jsonify({
            "status": "ERROR",
            "message": "An internal system error occurred.",
            "code": 500
        }), 500


@access_bp.route("/requests", methods=["GET"])
@limiter.limit("20 per minute")
@jwt_required()
@actor_types_required("patient", "staff")
@permissions_required("access:view_requests")
def view_all_requests_endpoint():
    claims = get_jwt()
    actor_type = claims.get("actor_type")
    actor_id = as_uuid(get_jwt_identity())

    try:
        if actor_type == "patient":
            patient = db.session.get(Patient, actor_id)
            if not patient:
                return jsonify({
                    "status": "ERROR",
                    "message": "Patient record not found.",
                    "code": 404
                }), 404

            stmt = (
                db.select(Requests)
                .where(Requests.patient_public_id == patient.public_id)
                .order_by(desc(Requests.created_at))
            )
            message = "Retrieved all access requests successfully!"
        else:
            staff = db.session.get(Staff, actor_id)
            if not staff:
                return jsonify({
                    "status": "ERROR",
                    "message": "Staff record not found.",
                    "code": 404
                }), 404

            stmt = (
                db.select(Requests)
                .where(Requests.staff_id == staff.id)
                .order_by(desc(Requests.created_at))
            )
            message = "Retrieved all access requests for staff successfully!"

        status_filter = request.args.get("status")
        if status_filter:
            normalized = str(status_filter).strip().capitalize()
            stmt = stmt.where(Requests.status == normalized)

        access_requests = db.session.scalars(stmt).all()

        return jsonify({
            "status": "SUCCESS",
            "code": 200,
            "message": message,
            "count": len(access_requests),
            "data": [req.to_dict() for req in access_requests]
        }), 200
    except Exception as e:
        logger.error("Error fetching access requests: %s", str(e), exc_info=True)
        return jsonify({
            "status": "ERROR",
            "message": "An internal system error occurred.",
            "code": 500
        }), 500


@access_bp.route("/requests/<request_id>", methods=["GET"])
@limiter.limit("20 per minute")
@jwt_required()
@actor_types_required("patient", "staff")
@permissions_required("access:view_requests")
def view_request_endpoint(request_id):
    claims = get_jwt()
    actor_type = claims.get("actor_type")
    actor_id = as_uuid(get_jwt_identity())
    parsed_id = as_uuid(request_id)

    if parsed_id is None:
        return jsonify({
            "status": "ERROR",
            "message": "Invalid request ID.",
            "code": 400
        }), 400

    access_request = db.session.get(Requests, parsed_id)
    if not access_request:
        return jsonify({
            "status": "ERROR",
            "message": "Request record not found.",
            "code": 404
        }), 404

    if actor_type == "patient":
        patient = db.session.get(Patient, actor_id)
        if not patient or access_request.patient_public_id != patient.public_id:
            return jsonify({
                "status": "ERROR",
                "message": "Request record not found.",
                "code": 404
            }), 404
    else:
        staff = db.session.get(Staff, actor_id)
        if not staff or access_request.staff_id != staff.id:
            return jsonify({
                "status": "ERROR",
                "message": "Request record not found.",
                "code": 404
            }), 404

    return jsonify({
        "status": "SUCCESS",
        "message": "Access request retrieved successfully.",
        "data": access_request.to_dict(),
        "code": 200
    }), 200


@access_bp.route("/requests/<request_id>/review", methods=["POST"])
@limiter.limit("10 per minute")
@jwt_required()
@actor_types_required("patient")
@permissions_required("access:review")
def review_request_endpoint(request_id):
    current_patient_id = as_uuid(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    raw_status = data.get("status") or request.args.get("status")
    decision = _normalize_review_status(raw_status)

    if not decision:
        logger.warning("Attempt to review requests with missing status.")
        return jsonify({
            "status": "ERROR",
            "message": "Missing or invalid status. Expected 'Approved' or 'Denied'.",
            "code": 400
        }), 400

    patient = db.session.get(Patient, current_patient_id)
    if not patient:
        logger.warning(
            "Patient with ID %s not found during reviewing request.",
            current_patient_id
        )
        return jsonify({
            "status": "ERROR",
            "message": "Patient record not found.",
            "code": 404
        }), 404

    parsed_id = as_uuid(request_id)
    if parsed_id is None:
        return jsonify({
            "status": "ERROR",
            "message": "Invalid request ID.",
            "code": 400
        }), 400

    access_request = db.session.get(Requests, parsed_id)
    if not access_request or access_request.patient_public_id != patient.public_id:
        logger.warning(
            "Request with ID %s not found during reviewing request.",
            request_id
        )
        return jsonify({
            "status": "ERROR",
            "message": "Request record not found.",
            "code": 404
        }), 404

    if access_request.status != RequestStatus.PENDING.value:
        return jsonify({
            "status": "ERROR",
            "message": f"This request has already been {access_request.status.lower()}.",
            "code": 409
        }), 409

    try:
        access_request.status = decision.value
        access_request.reviewed_at = lagos_now()

        grant_payload = None
        if decision == RequestStatus.APPROVED:
            grant_hours = int(current_app.config.get("ACCESS_GRANT_HOURS", 24))
            new_grant = AccessGrants(
                request_id=access_request.id,
                patient_public_id=access_request.patient_public_id,
                staff_id=access_request.staff_id,
                hospital_id=access_request.hospital_id,
                scope=access_request.scope,
                status=GrantStatus.GRANTED.value,
                expires_at=lagos_now() + timedelta(hours=grant_hours),
            )
            db.session.add(new_grant)
            db.session.flush()
            grant_payload = new_grant.to_dict()

        db.session.commit()

        return jsonify({
            "status": "UPDATED",
            "message": f"Access request {decision.value.lower()} successfully!",
            "data": {
                "request": access_request.to_dict(),
                "grant": grant_payload,
            },
            "code": 200
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error("Access review crash: %s", str(e), exc_info=True)
        return jsonify({
            "status": "ERROR",
            "message": "An internal system error occurred.",
            "code": 500
        }), 500


@access_bp.route("/grants", methods=["GET"])
@limiter.limit("20 per minute")
@jwt_required()
@actor_types_required("patient", "staff")
@permissions_required("access:view_requests")
def view_grants_endpoint():
    claims = get_jwt()
    actor_type = claims.get("actor_type")
    actor_id = as_uuid(get_jwt_identity())

    if actor_type == "patient":
        patient = db.session.get(Patient, actor_id)
        if not patient:
            return jsonify({
                "status": "ERROR",
                "message": "Patient record not found.",
                "code": 404
            }), 404
        stmt = db.select(AccessGrants).where(
            AccessGrants.patient_public_id == patient.public_id
        )
    else:
        staff = db.session.get(Staff, actor_id)
        if not staff:
            return jsonify({
                "status": "ERROR",
                "message": "Staff record not found.",
                "code": 404
            }), 404
        stmt = db.select(AccessGrants).where(
            AccessGrants.staff_id == staff.id
        )

    grants = db.session.scalars(
        stmt.order_by(desc(AccessGrants.created_at))
    ).all()

    return jsonify({
        "status": "SUCCESS",
        "code": 200,
        "message": "Access grants retrieved successfully.",
        "count": len(grants),
        "data": [grant.to_dict() for grant in grants]
    }), 200


@access_bp.route("/grants/<grant_id>/revoke", methods=["POST"])
@limiter.limit("10 per minute")
@jwt_required()
@actor_types_required("patient")
@permissions_required("access:revoke")
def revoke_grant_endpoint(grant_id):
    current_patient_id = as_uuid(get_jwt_identity())
    patient = db.session.get(Patient, current_patient_id)

    if not patient:
        return jsonify({
            "status": "ERROR",
            "message": "Patient record not found.",
            "code": 404
        }), 404

    parsed_id = as_uuid(grant_id)
    if parsed_id is None:
        return jsonify({
            "status": "ERROR",
            "message": "Invalid grant ID.",
            "code": 400
        }), 400

    grant = db.session.get(AccessGrants, parsed_id)
    if not grant or grant.patient_public_id != patient.public_id:
        return jsonify({
            "status": "ERROR",
            "message": "Access grant not found.",
            "code": 404
        }), 404

    if grant.status != GrantStatus.GRANTED.value:
        return jsonify({
            "status": "ERROR",
            "message": f"This grant is already {grant.status.lower()}.",
            "code": 409
        }), 409

    grant.status = GrantStatus.REVOKED.value
    db.session.commit()

    return jsonify({
        "status": "UPDATED",
        "message": "Access grant revoked successfully.",
        "data": grant.to_dict(),
        "code": 200
    }), 200
