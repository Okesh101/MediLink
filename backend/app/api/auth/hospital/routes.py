# app/api/auth/hospital/routes.py

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt, get_jwt_identity
import logging

from app import db, limiter
from app.models.Hospital import Hospital
from app.models.Role import Role
from app.models.TokenBlocklist import TokenBlocklist
from app.utils.decorators import permissions_required, actor_types_required
from app.utils.helpers import as_uuid

auth_hospital_bp = Blueprint("auth_hospital", __name__)
logger = logging.getLogger(__name__)


@auth_hospital_bp.route("/register", methods=["POST"])
@limiter.limit('10 per minute')
def register_endpoint():
    data = request.get_json() or {}

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

    phone = str(data.get('phone', '')).strip()
    if not phone.isdigit() or len(phone) != 11:
        logger.warning(
            "Attempt to register hospital with invalid phone number.")
        return jsonify({
            "status": "ERROR",
            "message": "Phone number must be exactly 11 digits",
            "code": 400
        }), 400

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

        created = db.session.get(Hospital, new_hospital.id)

        return jsonify({
            "status": "CREATED",
            "message": "Hospital registered successfully!",
            "data": created.to_dict(),
            "code": 201
        }), 201
    except IntegrityError as e:
        db.session.rollback()
        err_msg = str(e.orig)
        if "phone" in err_msg:
            message = "Phone number already registered."
        elif "reg_no" in err_msg:
            message = "Registration number already registered."
        elif "email" in err_msg:
            message = "Email already registered."
        else:
            logger.error(
                "Hospital registration integrity error: %s",
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
        logger.error("Hospital registration crash: %s", str(e), exc_info=True)
        return jsonify({
            "status": "ERROR",
            "message": "An internal system error occurred. Please try again later.",
            "code": 500
        }), 500


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

    hospital = db.session.execute(db.select(Hospital).filter_by(
        email=data['email'])).scalar_one_or_none()

    if not hospital or not hospital.check_password(data['password']):
        logger.warning("Attempt to login with invalid email or password.")
        return jsonify({
            "status": "ERROR",
            "code": 401,
            "message": "Invalid email or password"
        }), 401

    extra_claims = {"actor_type": "hospital_admin"}
    access_token = create_access_token(
        identity=str(hospital.id),
        additional_claims=extra_claims
    )
    refresh_token = create_refresh_token(
        identity=str(hospital.id),
        additional_claims=extra_claims
    )

    return jsonify({
        "status": "SUCCESS",
        "message": "Login successful!",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "hospital": hospital.to_dict(),
        "code": 200
    }), 200


@auth_hospital_bp.route("/me", methods=["GET"])
@limiter.limit('30 per minute')
@jwt_required()
@actor_types_required("hospital_admin")
@permissions_required("hospital:manage_profile")
def get_profile_endpoint():
    current_hospital_id = as_uuid(get_jwt_identity())
    hospital = db.session.get(Hospital, current_hospital_id)

    if not hospital:
        logger.warning(
            "Hospital with ID %s not found during profile retrieval.",
            current_hospital_id
        )
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


@auth_hospital_bp.route("/logout", methods=['POST'])
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
        "access_token": new_access_token,
        "code": 200
    }), 200
