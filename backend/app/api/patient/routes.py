# app/api/patient/routes.py

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

from app import db, limiter
from app.models.Patient import Patient
from app.models.PatientDetails import PatientDetails
from app.models.Loan import Loan
from app.models.MedicalRecords import LoanRequest
from app.models.Repayment import Repayment
from app.utils.decorators import permissions_required
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import logging

patient_bp = Blueprint("patient", __name__)
logger = logging.getLogger(__name__)


# api/v1/patient/kyc
@patient_bp.route("/kyc", methods=["POST"])
@limiter.limit('10 per minute')
@jwt_required()
@permissions_required("patient:submit_kyc")
def update_profile_endpoint():
    current_patient_id = get_jwt_identity()
    data = request.get_json() or {}

    required_fields = ['email', 'bvn', 'dob', 'next_of_kin_name', 'next_of_kin_number',
                       'next_of_kin_relationship', 'guarantor_name', 'guarantor_number',
                       'guarantor_relationship', 'guarantor_email']
    if not all(data.get(field) for field in required_fields):
        logger.warning(
            "Attempt to update profile with missing required fields.")
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
            "Attempt to update profile with invalid date format.")
        return jsonify({
            "status": "ERROR",
            "message": "Invalid date format. Use YYYY-MM-DD",
            "code": 400
        }), 400

    # BVN normalization verification
    bvn = str(data.get('bvn', '')).strip()
    if not bvn.isdigit() or len(bvn) != 11:
        logger.warning("Attempt to register with invalid BVN.")
        return jsonify({
            "status": "ERROR",
            "message": "BVN must be exactly 11 digits",
            "code": 400
        }), 400

    # Modern SQLAlchemy 2.0 select query execution syntax
    patient = db.session.get(Patient, current_patient_id)

    if not patient:
        logger.warning(
            f"Patient with ID {current_patient_id} not found during profile update.")
        return jsonify({
            "status": "ERROR",
            "code": 404,
            "message": "Patient not found"
        }), 404

    patient_details = PatientDetails(
        patient_id=current_patient_id,
        email=data['email'],
        bvn=bvn,
        dob=parsed_dob,
        next_of_kin_name=data['next_of_kin_name'],
        next_of_kin_number=data['next_of_kin_number'],
        next_of_kin_relationship=data['next_of_kin_relationship'],
        guarantor_name=data['guarantor_name'],
        guarantor_number=data['guarantor_number'],
        guarantor_relationship=data['guarantor_relationship'],
        guarantor_email=data['guarantor_email']
    )

    if not patient.is_verified:
        patient.is_verified = True

    try:
        db.session.add(patient_details)
        db.session.commit()
        return jsonify({
            "status": "SUCCESS",
            "message": "Patient KYC updated and verified successfully!",
            "code": 200
        }), 200
    except IntegrityError as e:
        db.session.rollback()
        # Check if the unique constraint failed for email or bvn code
        err_msg = str(e.orig)
        if "email" in err_msg:
            message = "System generated a duplicate email. Please try again."
        elif "bvn" in err_msg:
            message = "System generated a duplicate BVN. Please try again."
        else:
            message = "A record duplicate conflict occurred."

        return jsonify({
            "status": "ERROR",
            "message": message,
            "code": 409
        }), 409
    except Exception as e:
        db.session.rollback()
        # Log the actual raw error on your Kubuntu server logs securely
        logger.error(f"KYC insertion crash: {str(e)}", exc_info=True)
        return jsonify({
            "status": "ERROR",
            "message": "An internal system error occurred. Please try again later.",
            "code": 500
        }), 500


# api/v1/patient/loans
@patient_bp.route("/loans", methods=["GET"])
@limiter.limit('15 per minute')
@jwt_required()
@permissions_required("loan:history")
def view_patient_loans():
    """Fetch all actual active/disbursed loans belonging to the authenticated patient."""
    current_patient_id = get_jwt_identity()

    patient = db.session.get(Patient, current_patient_id)
    if not patient:
        logger.warning(f"Patient record {current_patient_id} not found.")
        return jsonify({
            "status": "ERROR",
            "code": 404,
            "message": f"Patient with ID {current_patient_id} not found."
        }), 404

    try:
        # Join Loan with LoanRequest to query specifically by patient_id
        stmt = (
            select(Loan)
            .join(LoanRequest, Loan.request_id == LoanRequest.id)
            .where(LoanRequest.patient_public_id == patient.public_id)
            .order_by(Loan.created_at.desc())
        )
        loans = db.session.scalars(stmt).all()

        return jsonify({
            "status": "SUCCESS",
            "message": "Patient loans retrieved successfully.",
            "data": [loan.to_dict() for loan in loans],
            "code": 200
        }), 200

    except Exception as e:
        logger.error(f"Error fetching patient loans: {str(e)}", exc_info=True)
        return jsonify({
            "status": "ERROR",
            "message": "Failed to retrieve loan records.",
            "code": 500
        }), 500


# api/v1/patient/loans/repayment
@patient_bp.route("/loans/repayment", methods=["GET"])
@limiter.limit('15 per minute')
@jwt_required()
@permissions_required("loan:view_repayment")
def view_patient_repayments():
    """Fetch repayment plans across all active loans for the authenticated patient."""
    current_patient_id = get_jwt_identity()

    patient = db.session.get(Patient, current_patient_id)
    if not patient:
        logger.warning(f"Patient record {current_patient_id} not found.")
        return jsonify({
            "status": "ERROR",
            "code": 404,
            "message": f"Patient with ID {current_patient_id} not found."
        }), 404

    # Optional: Filter by specific active loan if passed in query params
    loan_id = request.args.get("loan_id")

    try:
        stmt = (
            select(Repayment)
            .join(Loan, Repayment.loan_id == Loan.id)
            .join(LoanRequest, Loan.request_id == LoanRequest.id)
            .where(LoanRequest.patient_public_id == patient.public_id)
        )

        if loan_id:
            stmt = stmt.where(Loan.id == loan_id)

        stmt = stmt.order_by(Repayment.next_due_date.asc())
        repayments = db.session.scalars(stmt).all()

        return jsonify({
            "status": "SUCCESS",
            "message": "Repayment schedules retrieved successfully.",
            "data": [repayment.to_dict() for repayment in repayments],
            "code": 200
        }), 200

    except Exception as e:
        logger.error(
            f"Error fetching repayment plans: {str(e)}", exc_info=True)
        return jsonify({
            "status": "ERROR",
            "message": "Failed to retrieve repayment plans.",
            "code": 500
        }), 500
