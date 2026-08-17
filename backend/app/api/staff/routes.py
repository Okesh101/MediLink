# app/api/staff/routes.py

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging

from app import db, limiter
from app.models.Hospital import Hospital
from app.models.Staff import Staff
from app.models.Role import Role
from app.utils.decorators import permissions_required
from app.utils.types import Sex

staff_bp = Blueprint("staff", __name__)
logger = logging.getLogger(__name__)


# api/v1/staff/doctor
@staff_bp.route("/doctor", methods=["POST"])
@limiter.limit('10 per minute')
@jwt_required()
@permissions_required("hospital:manage_staff")
def onboard_doctor_endpoint():
    current_hospital_id = get_jwt_identity()
    data = request.get_json() or {}

    # Strict dictionary presence validation (replaces old unsafe all() evaluation)
    required_fields = ['name', 'email', 'phone', 'nin', 'sex']
    if not all(data.get(field) for field in required_fields):
        logger.warning(
            "Attempt to register doctor with missing required fields.")
        return jsonify({
            "status": "ERROR",
            "message": "Missing required fields",
            "code": 400
        }), 400

    # Phone normalization verification
    phone = str(data.get('phone', '')).strip()
    if not phone.isdigit() or len(phone) != 11:
        logger.warning(
            "Attempt to register doctor with invalid phone number.")
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
        logger.warning(
            "Attempt to register with invalid sex. Must be male or female.")
        return jsonify({
            "status": "ERROR",
            "message": "Sex must be either male or female.",
            "code": 400
        }), 400

    # Check email uniqueness before executing heavy operations
    if db.session.execute(db.select(Staff).filter_by(email=data['email'])).scalar_one_or_none():
        logger.warning("Attempt to register with existing email.")
        return jsonify({
            "status": "ERROR",
            "message": "Email already registered",
            "code": 409
        }), 409

    hospital = db.session.get(Hospital, current_hospital_id)

    if not hospital:
        logger.warning(
            f"Hospital with ID {current_hospital_id} not found during doctor creation.")
        return jsonify({
            "status": "ERROR",
            "code": 404,
            "message": "Hospital not found"
        }), 404

    new_staff = Staff(
        hospital_id=current_hospital_id,
        name=data['name'],
        email=data['email'],
        phone=phone,
        sex=real_sex,
        nin=nin,
    )
    new_staff.set_password(data['password'])

    # Setup roles safely
    doctor_role = db.session.execute(
        db.select(Role).filter_by(name="Doctor")).scalar_one_or_none()

    if not doctor_role:
        logger.warning(
            "Attempting to assign Doctor role which is missing from the database.")
        return jsonify({
            "status": "ERROR",
            "code": 500,
            "message": "System critical role ('Doctor') is missing from the database."
        }), 500

    try:
        db.session.add(new_staff)
        db.session.flush()

        new_staff.assign_role(doctor_role)
        db.session.commit()

        return jsonify({
            "status": "CREATED",
            "message": "Doctor registered successfully!",
            "code": 201
        }), 201
    except IntegrityError as e:
        db.session.rollback()
        # Check if the unique constraint failed for email, phone or nin
        err_msg = str(e.orig)
        if "phone" in err_msg:
            message = "System generated a duplicate phone number. Please try again."
        elif "nin" in err_msg:
            message = "System generated a duplicate NIN. Please try again."
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
        logger.error(
            f"Hospital creating doctor crash: {str(e)}", exc_info=True)
        return jsonify({
            "status": "ERROR",
            "message": "An internal system error occurred. Please try again later.",
            "code": 500
        }), 500
