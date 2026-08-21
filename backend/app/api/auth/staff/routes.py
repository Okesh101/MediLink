# app/api/auth/staff/routes.py

from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt, get_jwt_identity
import logging

from app import db, limiter
from app.models.Staff import Staff
from app.models.TokenBlocklist import TokenBlocklist
from app.utils.decorators import permissions_required, actor_types_required
from app.utils.helpers import as_uuid

auth_staff_bp = Blueprint("auth_staff", __name__)
logger = logging.getLogger(__name__)


@auth_staff_bp.route("/login", methods=["POST"])
@limiter.limit('10 per minute')
def login_endpoint():
    data = request.get_json() or {}

    if not data.get('email') or not data.get('password'):
        logger.warning("Attempt to login with missing required fields.")
        return jsonify({
            "status": "ERROR",
            "message": "Missing required fields",
            "code": 400
        }), 400

    staff = db.session.execute(db.select(Staff).filter_by(
        email=data['email'])).scalar_one_or_none()

    if not staff or not staff.check_password(data['password']):
        logger.warning("Attempt to login with invalid email or password.")
        return jsonify({
            "status": "ERROR",
            "code": 401,
            "message": "Invalid email or password"
        }), 401

    extra_claims = {"actor_type": "staff"}
    access_token = create_access_token(
        identity=str(staff.id),
        additional_claims=extra_claims
    )
    refresh_token = create_refresh_token(
        identity=str(staff.id),
        additional_claims=extra_claims
    )

    return jsonify({
        "status": "SUCCESS",
        "message": "Login successful!",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "staff": staff.to_dict(),
        "code": 200
    }), 200


@auth_staff_bp.route("/me", methods=["GET"])
@limiter.limit('30 per minute')
@jwt_required()
@actor_types_required("staff")
@permissions_required("staff:manage_profile")
def get_profile_endpoint():
    current_staff_id = as_uuid(get_jwt_identity())
    staff = db.session.get(Staff, current_staff_id)

    if not staff:
        logger.warning(
            "Staff with ID %s not found during profile retrieval.",
            current_staff_id
        )
        return jsonify({
            "status": "ERROR",
            "code": 404,
            "message": "Staff not found"
        }), 404

    return jsonify({
        "status": "SUCCESS",
        "data": staff.to_dict(),
        "code": 200,
        "message": "Staff profile data retrieved successfully"
    }), 200


@auth_staff_bp.route("/logout", methods=['POST'])
@limiter.limit('30 per minute')
@jwt_required()
def logout_endpoint():
    access_claims = get_jwt()
    access_jti = access_claims['jti']
    db.session.add(TokenBlocklist(jti=access_jti))

    refresh_token = request.headers.get("X-Refresh-Token")

    if refresh_token:
        from flask_jwt_extended import decode_token
        try:
            refresh_claims = decode_token(refresh_token)
            refresh_jti = refresh_claims.get('jti')

            if refresh_claims.get('type') == 'refresh' and refresh_jti:
                db.session.add(TokenBlocklist(jti=refresh_jti))
        except Exception:
            pass

    db.session.commit()

    return jsonify({
        "status": "SUCCESS",
        "code": 200,
        "message": "Logged out successfully. All session tokens have been permanently revoked."
    }), 200


@auth_staff_bp.route("/refresh", methods=['POST'])
@limiter.limit('10 per minute')
@jwt_required(refresh=True)
def refresh_endpoint():
    current_staff_id = get_jwt_identity()
    new_access_token = create_access_token(
        identity=current_staff_id,
        additional_claims={
            "actor_type": "staff"
        })
    return jsonify({
        "status": "SUCCESS",
        "access_token": new_access_token,
        "code": 200
    }), 200
