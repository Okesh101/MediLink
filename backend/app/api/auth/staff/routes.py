# app/api/auth/staff/routes.py

from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt, get_jwt_identity
import logging

from app import db, limiter
from app.models.Staff import Staff
from app.models.TokenBlocklist import TokenBlocklist
from app.utils.decorators import permissions_required

auth_staff_bp = Blueprint("auth_staff", __name__)
logger = logging.getLogger(__name__)


# api/v1/auth/staff/login
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

    # Modern SQLAlchemy 2.0 select query execution syntax
    staff = db.session.execute(db.select(Staff).filter_by(
        email=data['email'])).scalar_one_or_none()

    if not staff or not staff.check_password(data['password']):
        logger.warning("Attempt to login with invalid email or password.")
        return jsonify({
            "status": "ERROR",
            "code": 401,
            "message": "Invalid email or password"
        }), 401

    access_token = create_access_token(
        identity=str(staff.id),
        additional_claims={
            "actor_type": "staff"
        })
    refresh_token = create_refresh_token(identity=str(staff.id))

    return jsonify({
        "status": "SUCCESS",
        "message": "Login successful!",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "staff": staff.to_dict(),
        "code": 200
    }), 200


# api/v1/auth/staff/me
@auth_staff_bp.route("/me", methods=["GET"])
@limiter.limit('30 per minute')
@jwt_required()
@permissions_required("staff:manage_personal_data")
def get_profile_endpoint():
    current_staff_id = get_jwt_identity()

    # Modern execution replacement for deprecated .query.get()
    staff = db.session.get(Staff, current_staff_id)

    if not staff:
        logger.warning(
            f"Staff with ID {current_staff_id} not found during profile retrieval.")
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


# api/v1/auth/staff/logout
@auth_staff_bp.route("/logout", methods=['POST'])
@limiter.limit('30 per minute')
@jwt_required()
def logout_endpoint():
    # 1. Revoke the active Access Token (from Header)
    access_claims = get_jwt()
    access_jti = access_claims['jti']
    db.session.add(TokenBlocklist(jti=access_jti))

    # 2. Grab Refresh Token from custom header
    refresh_token = request.headers.get("X-Refresh-Token")

    if refresh_token:
        from flask_jwt_extended import decode_token
        try:
            # Safely decode the token claims without verifying signatures again
            refresh_claims = decode_token(refresh_token)
            refresh_jti = refresh_claims.get('jti')

            # Double check that it actually is a refresh token type
            if refresh_claims.get('type') == 'refresh' and refresh_jti:
                db.session.add(TokenBlocklist(jti=refresh_jti))
        except Exception:
            # If token is completely malformed or corrupted, skip silently
            pass

    db.session.commit()

    return jsonify({
        "status": "SUCCESS",
        "code": 200,
        "message": "Logged out successfully. All session tokens have been permanently revoked."
    }), 200


# api/v1/auth/staff/refresh
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
        "access_token": new_access_token
    }), 200
