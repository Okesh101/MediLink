# app/api/staff/routes.py

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging

from app import db, limiter
from app.models.Hospital import Hospital
from app.models.Staff import Staff
from app.models.Role import Role
from app.utils.decorators import permissions_required, actor_types_required
from app.utils.helpers import as_uuid
from app.utils.types import Sex

staff_bp = Blueprint("staff", __name__)
logger = logging.getLogger(__name__)


@staff_bp.route("/doctor", methods=["POST"])
@limiter.limit('10 per minute')
@jwt_required()
@actor_types_required("hospital_admin")
@permissions_required("hospital:manage_staff")
def onboard_doctor_endpoint():
    current_hospital_id = as_uuid(get_jwt_identity())
    data = request.get_json() or {}

    required_fields = ['name', 'email', 'phone', 'nin', 'sex', 'password']
    if not all(data.get(field) for field in required_fields):
        logger.warning(
            "Attempt to register doctor with missing required fields.")
        return jsonify({
            "status": "ERROR",
            "message": "Missing required fields",
            "code": 400
        }), 400

    phone = str(data.get('phone', '')).strip()
    if not phone.isdigit() or len(phone) != 11:
        logger.warning(
            "Attempt to register doctor with invalid phone number.")
        return jsonify({
            "status": "ERROR",
            "message": "Phone number must be exactly 11 digits",
            "code": 400
        }), 400

    nin = str(data.get('nin', '')).strip()
    if not nin.isdigit() or len(nin) != 11:
        logger.warning("Attempt to register with invalid NIN.")
        return jsonify({
            "status": "ERROR",
            "message": "NIN must be exactly 11 digits",
            "code": 400
        }), 400

    sex = str(data.get('sex', '')).strip().lower()
    if sex in ('f', 'female'):
        real_sex = Sex.FEMALE.value
    elif sex in ('m', 'male'):
        real_sex = Sex.MALE.value
    else:
        logger.warning(
            "Attempt to register with invalid sex. Must be male or female.")
        return jsonify({
            "status": "ERROR",
            "message": "Sex must be either male or female.",
            "code": 400
        }), 400

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
            "Hospital with ID %s not found during doctor creation.",
            current_hospital_id
        )
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

        created = db.session.get(Staff, new_staff.id)

        return jsonify({
            "status": "CREATED",
            "message": "Doctor registered successfully!",
            "data": created.to_dict(),
            "code": 201
        }), 201
    except IntegrityError as e:
        db.session.rollback()
        err_msg = str(e.orig)
        if "phone" in err_msg:
            message = "Phone number already registered."
        elif "nin" in err_msg:
            message = "NIN already registered."
        elif "email" in err_msg:
            message = "Email already registered."
        else:
            logger.error(
                "Doctor registration integrity error: %s",
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
        logger.error("Hospital creating doctor crash: %s", str(e), exc_info=True)
        return jsonify({
            "status": "ERROR",
            "message": "An internal system error occurred. Please try again later.",
            "code": 500
        }), 500


@staff_bp.route("", methods=["GET"])
@limiter.limit('20 per minute')
@jwt_required()
@actor_types_required("hospital_admin")
@permissions_required("hospital:view_staff")
def list_staff_endpoint():
    current_hospital_id = as_uuid(get_jwt_identity())
    hospital = db.session.get(Hospital, current_hospital_id)

    if not hospital:
        return jsonify({
            "status": "ERROR",
            "code": 404,
            "message": "Hospital not found"
        }), 404

    staff_members = db.session.scalars(
        db.select(Staff)
        .where(Staff.hospital_id == current_hospital_id)
        .order_by(Staff.created_at.desc())
    ).all()

    return jsonify({
        "status": "SUCCESS",
        "code": 200,
        "message": "Hospital staff retrieved successfully.",
        "count": len(staff_members),
        "data": [member.to_dict() for member in staff_members]
    }), 200


@staff_bp.route("/<staff_id>", methods=["GET"])
@limiter.limit('20 per minute')
@jwt_required()
@actor_types_required("hospital_admin")
@permissions_required("hospital:view_staff")
def get_staff_endpoint(staff_id):
    current_hospital_id = as_uuid(get_jwt_identity())
    parsed_staff_id = as_uuid(staff_id)

    if parsed_staff_id is None:
        return jsonify({
            "status": "ERROR",
            "code": 400,
            "message": "Invalid staff ID."
        }), 400

    staff = db.session.get(Staff, parsed_staff_id)
    if not staff or staff.hospital_id != current_hospital_id:
        return jsonify({
            "status": "ERROR",
            "code": 404,
            "message": "Staff not found."
        }), 404

    return jsonify({
        "status": "SUCCESS",
        "code": 200,
        "message": "Staff retrieved successfully.",
        "data": staff.to_dict()
    }), 200
