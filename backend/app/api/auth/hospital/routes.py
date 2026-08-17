# app/api/auth/hospital/routes.py

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt, get_jwt_identity
import logging

from app import db, limiter
from app.models.Hospital import Hospital
from app.models.Role import Role
from app.models.TokenBlocklist import TokenBlocklist
from app.utils.decorators import permissions_required

auth_hospital_bp = Blueprint("auth_hospital", __name__)
logger = logging.getLogger(__name__)


# api/v1/auth/hospital/register
@auth_hospital_bp.route("/register", methods=["POST"])
@limiter.limit('10 per minute')
def register_endpoint():
    data = request.get_json() or {}

    # Strict dictionary presence validation (replaces old unsafe all() evaluation)
    required_fields = ['reg_no', 'name', 'email', 'phone',
                       'address', 'password']
    if not all(data.get(field) for field in required_fields):
        logger.warning(
            "Attempt to register hospital with missing required fields.")
        return jsonify({
            "status": "ERROR",
            "message": "Missing required fields",
            "code": 400
        }), 400

    # Phone normalization verification
    phone = str(data.get('phone', '')).strip()
    if not phone.isdigit() or len(phone) != 11:
        logger.warning(
            "Attempt to register hospital with invalid phone number.")
        return jsonify({
            "status": "ERROR",
            "message": "Phone number must be exactly 11 digits",
            "code": 400
        }), 400

    # Call HERMAA API for verification of hospital registration number (reg_no) and other details

    # Check reg_no uniqueness before executing heavy operations
    if db.session.execute(db.select(Hospital).filter_by(reg_no=data['reg_no'])).scalar_one_or_none():
        logger.warning("Attempt to register with existing reg_no.")
        return jsonify({
            "status": "ERROR",
            "message": "Registration number already registered",
            "code": 409
        }), 409

    new_hospital = Hospital(
        reg_no=data['reg_no'],
        name=data['name'],
        email=data['email'],
        phone=phone,
        address=data['address']
    )
    new_hospital.set_password(data['password'])

    # Setup roles safely
    hospital_admin_role = db.session.execute(
        db.select(Role).filter_by(name="Hospital Admin")).scalar_one_or_none()

    if not hospital_admin_role:
        logger.warning(
            "Attempting to assign Hospital Admin role which is missing from the database.")
        return jsonify({
            "status": "ERROR",
            "code": 500,
            "message": "System critical role ('Hospital Admin') is missing from the database."
        }), 500

    try:
        db.session.add(new_hospital)
        db.session.flush()

        new_hospital.assign_role(hospital_admin_role)
        db.session.commit()

        return jsonify({
            "status": "CREATED",
            "message": "Hospital registered successfully!",
            "code": 201
        }), 201
    except IntegrityError as e:
        db.session.rollback()
        # Check if the unique constraint failed for phone or reg_no or email
        err_msg = str(e.orig)
        if "phone" in err_msg:
            message = "System generated a duplicate phone number. Please try again."
        elif "reg_no" in err_msg:
            message = "System generated a duplicate registration number. Please try again."
        elif "email" in err_msg:
            message = "System generated a duplicate email. Please try again."
        else:
            logger.error(
                "Patient registration integrity error: %s",
                e,
                exc_info=True
            )
            message = "A database conflict occurred."

        return jsonify({
            "status": "ERROR",
            "message": message,
            "code": 409
        }), 409
    except Exception as e:
        db.session.rollback()
        # Log the actual raw error on your Kubuntu server logs securely
        logger.error(f"Hospital registration crash: {str(e)}", exc_info=True)
        return jsonify({
            "status": "ERROR",
            "message": "An internal system error occurred. Please try again later.",
            "code": 500
        }), 500


# api/v1/auth/hospital/login
@auth_hospital_bp.route("/login", methods=["POST"])
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
    hospital = db.session.execute(db.select(Hospital).filter_by(
        email=data['email'])).scalar_one_or_none()

    if not hospital or not hospital.check_password(data['password']):
        logger.warning("Attempt to login with invalid email or password.")
        return jsonify({
            "status": "ERROR",
            "code": 401,
            "message": "Invalid email or password"
        }), 401

    access_token = create_access_token(
        identity=str(hospital.id),
        additional_claims={
            "actor_type": "hospital_admin"
        })
    refresh_token = create_refresh_token(identity=str(hospital.id))

    return jsonify({
        "status": "SUCCESS",
        "message": "Login successful!",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "hospital": hospital.to_dict(),
        "code": 200
    }), 200


# api/v1/auth/hospital/me
@auth_hospital_bp.route("/me", methods=["GET"])
@limiter.limit('30 per minute')
@jwt_required()
@permissions_required("hospital:manage_personal_data")
def get_profile_endpoint():
    current_hospital_id = get_jwt_identity()

    # Modern execution replacement for deprecated .query.get()
    hospital = db.session.get(Hospital, current_hospital_id)

    if not hospital:
        logger.warning(
            f"Hospital with ID {current_hospital_id} not found during profile retrieval.")
        return jsonify({
            "status": "ERROR",
            "code": 404,
            "message": "Hospital not found"
        }), 404

    return jsonify({
        "status": "SUCCESS",
        "data": hospital.to_dict(),
        "code": 200,
        "message": "Hospital profile data retrieved successfully"
    }), 200


# api/v1/auth/hospital/logout
@auth_hospital_bp.route("/logout", methods=['POST'])
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


# api/v1/auth/hospital/refresh
@auth_hospital_bp.route("/refresh", methods=['POST'])
@limiter.limit('10 per minute')
@jwt_required(refresh=True)
def refresh_endpoint():
    current_hospital_id = get_jwt_identity()
    new_access_token = create_access_token(
        identity=current_hospital_id,
        additional_claims={
            "actor_type": "hospital_admin"
        })
    return jsonify({
        "status": "SUCCESS",
        "access_token": new_access_token
    }), 200
