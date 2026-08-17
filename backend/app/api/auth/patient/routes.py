# app/api/auth/patient/routes.py

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt, get_jwt_identity
from datetime import datetime
import logging

from app import db, limiter
from app.models.Role import Role
from app.models.Patient import Patient
from app.models.TokenBlocklist import TokenBlocklist
from app.utils.decorators import permissions_required
from app.utils.types import Sex

auth_patient_bp = Blueprint("auth_patient", __name__)
logger = logging.getLogger(__name__)


# api/v1/auth/patient/register
@auth_patient_bp.route("/register", methods=["POST"])
@limiter.limit('10 per minute')
def register_endpoint():
    data = request.get_json() or {}

    # Strict dictionary presence validation (replaces old unsafe all() evaluation)
    required_fields = ['firstname', 'lastname',
                       'sex', 'phone', 'dob',
                       'nin', 'password']
    if not all(data.get(field) for field in required_fields):
        logger.warning("Attempt to register with missing required fields.")
        return jsonify({
            "status": "ERROR",
            "message": "Missing required fields",
            "code": 400
        }), 400

    raw_dob = data.get('dob')  # Frontend sends "1995-04-23"
    try:
        # Validate that the string strictly follows YYYY-MM-DD
        parsed_dob = datetime.strptime(raw_dob, '%Y-%m-%d').date()
    except ValueError:
        logger.warning(
            "Attempt to register patient profile with invalid date format.")
        return jsonify({
            "status": "ERROR",
            "message": "Invalid date format. Use YYYY-MM-DD",
            "code": 400
        }), 400

    # Phone normalization verification
    phone = str(data.get('phone', '')).strip()
    if not phone.isdigit() or len(phone) != 11:
        logger.warning("Attempt to register with invalid phone number.")
        return jsonify({
            "status": "ERROR",
            "message": "Phone number must be exactly 11 digits",
            "code": 400
        }), 400

    # NIN normalization verification
    nin = str(data.get('nin', '')).strip()
    if not nin.isdigit() or len(nin) != 11:
        logger.warning("Attempt to register with invalid NIN.")
        return jsonify({
            "status": "ERROR",
            "message": "NIN must be exactly 11 digits",
            "code": 400
        }), 400

    sex = str(data.get('sex', '')).strip().lower()
    if sex == 'f' or sex == 'female':
        real_sex = Sex.FEMALE.value
    elif sex == 'm' or sex == 'male':
        real_sex = Sex.MALE.value
    else:
        logger.warning("Attempt to register with invalid sex. Must be male or female.")
        return jsonify({
            "status": "ERROR",
            "message": "Sex must be either male or female.",
            "code": 400
        }), 400

    # Check phone uniqueness before executing heavy operations
    if db.session.execute(db.select(Patient).filter_by(phone=data['phone'])).scalar_one_or_none():
        logger.warning("Attempt to register with existing phone.")
        return jsonify({
            "status": "ERROR",
            "message": "Phone number already registered",
            "code": 409
        }), 409

    new_patient = Patient(
        firstname=data['firstname'],
        lastname=data['lastname'],
        sex=real_sex,
        phone=phone,
        dob=parsed_dob,
        nin=nin,
        email=data.get('email') if data.get('email') else None
    )
    new_patient.set_password(data['password'])

    # Setup roles safely
    patient_role = db.session.execute(
        db.select(Role).filter_by(name="Patient")).scalar_one_or_none()

    if not patient_role:
        logger.warning(
            "Attempting to assign Patient role which is missing from the database.")
        return jsonify({
            "status": "ERROR",
            "code": 500,
            "message": "System critical role ('Patient') is missing from the database."
        }), 500

    try:
        db.session.add(new_patient)
        db.session.flush()

        new_patient.assign_role(patient_role)
        db.session.commit()

        return jsonify({
            "status": "CREATED",
            "message": "Patient registered successfully!",
            "code": 201
        }), 201
    except IntegrityError as e:
        db.session.rollback()
        # Check if the unique constraint failed for phone or nin code
        err_msg = str(e.orig)
        if "phone" in err_msg:
            message = "Phone number already registered."
        elif "nin" in err_msg:
            message = "NIN already registered."
        elif "email" in err_msg:
            message = "Email already registered."
        elif "public_id" in err_msg:
            message = "Generated public ID already exists. Please try again."
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
        logger.error(f"Registration crash: {str(e)}", exc_info=True)
        return jsonify({
            "status": "ERROR",
            "message": "An internal system error occurred. Please try again later.",
            "code": 500
        }), 500


# api/v1/auth/patient/login
@auth_patient_bp.route("/login", methods=["POST"])
@limiter.limit('10 per minute')
def login_endpoint():
    data = request.get_json() or {}

    if not data.get('phone') or not data.get('password'):
        logger.warning("Attempt to login with missing required fields.")
        return jsonify({
            "status": "ERROR",
            "message": "Missing required fields",
            "code": 400
        }), 400

    # Modern SQLAlchemy 2.0 select query execution syntax
    patient = db.session.execute(db.select(Patient).filter_by(
        phone=data['phone'])).scalar_one_or_none()

    if not patient or not patient.check_password(data['password']):
        logger.warning("Attempt to login with invalid phone or password.")
        return jsonify({
            "status": "ERROR",
            "code": 401,
            "message": "Invalid phone or password"
        }), 401

    access_token = create_access_token(
        identity=str(patient.id),
        additional_claims={
            "actor_type": "patient"
        }
    )
    refresh_token = create_refresh_token(identity=str(patient.id))

    return jsonify({
        "status": "SUCCESS",
        "message": "Login successful!",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "patient": patient.to_dict(),
        "code": 200
    }), 200


# api/v1/auth/patient/me
@auth_patient_bp.route("/me", methods=["GET"])
@limiter.limit('30 per minute')
@jwt_required()
@permissions_required("patient:manage_personal_data")
def get_profile_endpoint():
    current_patient_id = get_jwt_identity()

    # Modern execution replacement for deprecated .query.get()
    patient = db.session.get(Patient, current_patient_id)

    if not patient:
        logger.warning(
            f"Patient with ID {current_patient_id} not found during profile retrieval.")
        return jsonify({
            "status": "ERROR",
            "code": 404,
            "message": "Patient not found"
        }), 404

    return jsonify({
        "status": "SUCCESS",
        "data": patient.to_dict(),
        "code": 200,
        "message": "Profile data retrieved successfully"
    }), 200


# api/v1/auth/patient/logout
@auth_patient_bp.route("/logout", methods=['POST'])
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


# api/v1/auth/patient/refresh
@auth_patient_bp.route("/refresh", methods=['POST'])
@limiter.limit('20 per minute')
@jwt_required(refresh=True)
def refresh_endpoint():
    current_patient_id = get_jwt_identity()
    new_access_token = create_access_token(
        identity=current_patient_id,
        additional_claims={
            "actor_type": "patient"
        })
    return jsonify({
        "status": "SUCCESS",
        "access_token": new_access_token
    }), 200
