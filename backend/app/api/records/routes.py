# app/api/loan/routes.py

from flask import Blueprint, jsonify, request
from sqlalchemy import func, case, desc
import logging
import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from dotenv import load_dotenv

from app import db, limiter
from app.models.Staff import Staff
from app.models.Hospital import Hospital
from app.models.LoanRequest import LoanRequest
from app.models.Patient import Patient
from app.models.Loan import Loan
from app.models.Repayment import Repayment
from app.models.RequestDocuments import RequestDocuments
from app.utils.types import UrgencyStatus, LoanRequestStatus, LoanStatus
from app.utils.decorators import permissions_required, _get_current_actor
from app.services.cloudinary.cloudinary import upload_file_to_cloudinary
from flask_jwt_extended import jwt_required, get_jwt_identity

loan_bp = Blueprint("loan", __name__)
logger = logging.getLogger(__name__)
load_dotenv()


# Doctor Endpoint: Request for loan on behalf of patient
# api/v1/loan/request
@loan_bp.route("/request", methods=["POST"])
@limiter.limit('15 per minute')
@jwt_required()
@permissions_required("loan:apply")
def request_loan_endpoint():
    current_doctor_id = get_jwt_identity()

    form = request.form
    files = request.files.getlist('documents')
    # Parallel array from frontend
    titles = request.form.getlist('document_titles')

    required_fields = ['patient_public_id', 'diagnosis', 'urgency', 'estimated_cost',
                       'cost_breakdown', 'requested_repayment', 'time_before_repayment']

    if not all(form.get(field) for field in required_fields):
        logger.warning(
            "Attempt to proceed in loan request with missing fields.")
        return jsonify({
            "status": "ERROR",
            "message": "Missing required fields.",
            "code": 400
        }), 400

    # Parse JSON cost breakdown string
    try:
        cost_breakdown_data = json.loads(form['cost_breakdown'])
    except (ValueError, TypeError):
        logger.warning(
            "Attempt to proceed in loan request with malformed codt_breakdown JSON format.")
        return jsonify({
            "status": "ERROR",
            "message": "Invalid cost_breakdown format. Must be a valid JSON array or object.",
            "code": 400
        }), 400

    # Urgency Normalization
    urgency_raw = form['urgency'].strip().lower()
    if urgency_raw == "medium":
        cleaned_urgency = UrgencyStatus.MEDIUM.value
    elif urgency_raw == "critical":
        cleaned_urgency = UrgencyStatus.CRITICAL.value
    else:
        cleaned_urgency = UrgencyStatus.LOW.value

    # Patient Lookup
    cleaned_public_id = form['patient_public_id'].strip().replace(
        '-', '').upper()
    patient = db.session.scalar(
        db.select(Patient).where(
            func.replace(Patient.public_id, '-', '') == cleaned_public_id
        )
    )
    if not patient:
        logger.warning(
            f"Patient with public ID {cleaned_public_id} not found during loan request.")
        return jsonify({
            "status": "ERROR",
            "message": "Patient not found.",
            "code": 404
        }), 404

    doctor = db.session.get(Staff, current_doctor_id)
    if not doctor:
        logger.warning(
            f"Doctor with ID {current_doctor_id} not found during loan request.")
        return jsonify({
            "status": "ERROR",
            "message": "Doctor record not found.",
            "code": 404
        }), 404

    try:
        # Step 1: Create the Loan Request
        new_loan_request = LoanRequest(
            doctor_id=current_doctor_id,
            hospital_id=doctor.hospital_id,
            patient_public_id=patient.public_id,
            diagnosis=form['diagnosis'],
            urgency=cleaned_urgency,
            estimated_cost=float(form['estimated_cost']),
            cost_breakdown=cost_breakdown_data,
            requested_repayment_months=int(form['requested_repayment']),
            time_before_repayment_months=int(form['time_before_repayment'])
        )
        db.session.add(new_loan_request)
        db.session.flush()  # Generates new_loan_request.id for child FKs

        # Step 2: Upload Files & Match Custom Titles via zip()
        uploaded_doc_records = []

        # zip() pairs each file with its custom title, falling back gracefully
        for index, file in enumerate(files):
            if file and file.filename != '':
                # Use custom title from frontend; fallback to original filename if omitted
                custom_title = (
                    titles[index].strip()
                    if index < len(titles) and titles[index].strip()
                    else file.filename
                )

                # Upload to Cloudinary
                doc_url = upload_file_to_cloudinary(
                    file, folder="loan_documents")
                if not doc_url:
                    db.session.rollback()
                    logger.error(
                        f"Cloudinary upload failed for document: {custom_title}")
                    return jsonify({
                        "status": "ERROR",
                        "message": f"Failed to upload document: {custom_title}",
                        "code": 500
                    }), 500

                # Create document record with custom title
                doc_record = RequestDocuments(
                    request_id=new_loan_request.id,
                    title=custom_title,
                    doc_url=doc_url
                )
                uploaded_doc_records.append(doc_record)

        if uploaded_doc_records:
            db.session.add_all(uploaded_doc_records)
        new_loan_request.status = LoanRequestStatus.UNDER_REVIEW.value

        db.session.commit()

        return jsonify({
            "status": "CREATED",
            "message": "Loan request created and documents attached successfully!",
            "data": new_loan_request.to_dict(),
            "code": 201
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Loan creation crash: {str(e)}", exc_info=True)
        return jsonify({
            "status": "ERROR",
            "message": "An internal system error occurred.",
            "code": 500
        }), 500


# Hospital Endpoint: View requests originating from the current actor's hospital
# api/v1/loan/hospital
@loan_bp.route("/hospital", methods=["GET"])
@limiter.limit('15 per minute')
@jwt_required()
@permissions_required("loan:manage_requests")
def view_hospital_loan_requests():
    """Retrieves all loan applications associated with the logged-in hospital/staff's hospital."""
    try:
        actor = _get_current_actor()
        if not actor:
            logger.warning("Missing actor when trying to view hospital loans.")
            return jsonify({
                "status": "ERROR",
                "message": "Actor missing",
                "code": 401
            }), 401

        # Resolve hospital_id depending on whether actor is Hospital or Staff
        hospital_id = getattr(actor, "id", None) if isinstance(
            actor, Hospital) else getattr(actor, "hospital_id", None)

        if not hospital_id:
            logger.warning(
                "Cannot determine hospital affiliation when trying to view hospital loans.")
            return jsonify({
                "status": "ERROR",
                "message": "Could not determine hospital affiliation.",
                "code": 400
            }), 400

        stmt = (
            db.select(LoanRequest)
            .where(LoanRequest.hospital_id == hospital_id)
            .order_by(desc(LoanRequest.created_at))
        )
        hospital_requests = db.session.scalars(stmt).all()

        return jsonify({
            "status": "SUCCESS",
            "code": 200,
            "message": "Retrieved all hospital loans successfully!",
            "count": len(hospital_requests),
            "data": [req.to_dict() for req in hospital_requests]
        }), 200

    except Exception as e:
        logger.error(
            f"Error fetching hospital loan requests: {str(e)}", exc_info=True)
        return jsonify({
            "status": "ERROR",
            "message": "An internal system error occurred.",
            "code": 500
        }), 500


# Super Admin Endpoint: View all loan requests (Prioritizes 'Under Review', then desc date)
# api/v1/loan
@loan_bp.route("", methods=["GET"])
@limiter.limit('25 per minute')
@jwt_required()
@permissions_required("loan:approve")
def view_all_loan_request():
    """Retrieves all loan requests across the system.

    Sorts 'Under Review' status to the top, followed by newest created dates.
    """
    try:
        # Custom SQL Case order: 'Under Review' -> 1, 'Submitted' -> 2, others -> 3
        priority_order = case(
            (LoanRequest.status == LoanRequestStatus.UNDER_REVIEW.value, 1),
            (LoanRequest.status == LoanRequestStatus.SUBMITTED.value, 2),
            else_=3
        )

        stmt = (
            db.select(LoanRequest)
            .order_by(priority_order, desc(LoanRequest.created_at))
        )

        requests_list = db.session.scalars(stmt).all()

        return jsonify({
            "status": "SUCCESS",
            "code": 200,
            "message": "All loan requests retrieved successfully!",
            "count": len(requests_list),
            "data": [req.to_dict() for req in requests_list]
        }), 200

    except Exception as e:
        logger.error(
            f"Error fetching super admin loan requests: {str(e)}", exc_info=True)
        return jsonify({
            "status": "ERROR",
            "message": "An internal system error occurred.",
            "code": 500
        }), 500


# Super Admin Review & State Machine Execution
# api/v1/loan/review
@loan_bp.route("/review", methods=["POST"])
@limiter.limit('15 per minute')
@jwt_required()
@permissions_required("loan:approve")
def review_loan_request():
    """Super Admin review endpoint: Approve, Reject, or Request Info on a loan application."""
    data = request.get_json() or {}

    request_id = data.get("request_id")
    # Expected: 'approve', 'reject', 'request_info', 'disburse'
    action = data.get("action")
    admin_notes = data.get("admin_notes", "").strip()

    if not request_id or not action:
        logger.warning(
            "Attempt to change loan requests status with missing fields.")
        return jsonify({
            "status": "ERROR",
            "message": "Both 'request_id' and 'action' are required.",
            "code": 400
        }), 400

    loan_request = db.session.get(LoanRequest, request_id)
    if not loan_request:
        logger.warning(
            "Attempt to change loan requests status with missing loan request.")
        return jsonify({
            "status": "ERROR",
            "message": "Loan request not found.",
            "code": 404
        }), 404

    try:
        action_lower = action.lower()

        # ACTION: Request More Info
        if action_lower == "request_info":
            loan_request.status = LoanRequestStatus.INFO_REQUESTED.value
            loan_request.admin_notes = admin_notes
            db.session.commit()
            return jsonify({
                "status": "SUCCESS",
                "message": "Status updated to 'Info Requested'.",
                "data": loan_request.to_dict(),
                "code": 200
            }), 200

        # ACTION: Reject
        elif action_lower == "reject":
            loan_request.status = LoanRequestStatus.REJECTED.value
            loan_request.admin_notes = admin_notes

            # Cancel loan record if it was previously generated
            if loan_request.loan:
                loan_request.loan.status = LoanStatus.CANCELLED.value

            db.session.commit()
            return jsonify({
                "status": "SUCCESS",
                "message": "Loan request rejected successfully.",
                "data": loan_request.to_dict(),
                "code": 200
            }), 200

        # ACTION: Approve (Moves to Loan table)
        elif action_lower == "approve":
            loan_request.status = LoanRequestStatus.APPROVED.value
            loan_request.admin_notes = admin_notes

            # Perform Interest Calculations
            principal = Decimal(str(loan_request.estimated_cost))
            rate = Decimal(str(os.getenv("CUSTOM_INTEREST_RATE")))
            interest_amount = principal * (rate / Decimal("100"))
            total_payable = principal + interest_amount

            # Create or update associated Loan record
            if not loan_request.loan:
                new_loan = Loan(
                    request_id=loan_request.id,
                    principal_amount=principal,
                    interest_rate=rate,
                    total_amount=total_payable,
                    balance=total_payable,
                    status=LoanStatus.PENDING.value
                )
                db.session.add(new_loan)
            else:
                # Recalculate if re-approving
                loan_request.loan.principal_amount = principal
                loan_request.loan.interest_rate = rate
                loan_request.loan.total_amount = total_payable
                loan_request.loan.balance = total_payable

            db.session.commit()
            return jsonify({
                "status": "SUCCESS",
                "message": f"Loan request approved with {rate}% interest applied and moved to Loan ledger.",
                "data": loan_request.to_dict(),
                "code": 200
            }), 200

        # ACTION: Disburse (Mock Webhook / Disburse Trigger) (Generates Repayment schedule based on total_amount)
        elif action_lower == "disburse":
            if loan_request.status != LoanRequestStatus.APPROVED.value or not loan_request.loan:
                logger.warning("Attempt to disburse unapproved loan.")
                return jsonify({
                    "status": "ERROR",
                    "message": "Only approved loans with an existing loan record can be disbursed.",
                    "code": 400
                }), 400

            active_loan = loan_request.loan
            active_loan.status = LoanStatus.DISBURSED.value

            # Instantiate Repayment schedule upon disbursement
            if not active_loan.repayment:
                repayment_months = loan_request.requested_repayment_months
                grace_period_months = loan_request.time_before_repayment_months

                # Calculate installmental amount
                installment_amt = round(
                    float(active_loan.total_amount) / max(repayment_months, 1), 2)

                # First payment due date after grace period
                due_date = datetime.now(
                    ZoneInfo("Africa/Lagos")).date() + relativedelta(months=grace_period_months)

                new_repayment = Repayment(
                    loan_id=active_loan.id,
                    frequency="Monthly",
                    installmental_amount=installment_amt,
                    total_installment=repayment_months,
                    next_due_date=due_date
                )
                db.session.add(new_repayment)

            db.session.commit()
            return jsonify({
                "status": "SUCCESS",
                "message": "Loan successfully disbursed and repayment schedule instantiated.",
                "data": loan_request.to_dict(),
                "code": 200
            }), 200

        else:
            logger.warning(
                "Attempt to review loan requests with invalid action.")
            return jsonify({
                "status": "ERROR",
                "message": f"Invalid review action: '{action}'. Expected 'approve', 'reject', 'request_info', or 'disburse'.",
                "code": 400
            }), 400

    except Exception as e:
        db.session.rollback()
        logger.error(f"Loan review execution crash: {str(e)}", exc_info=True)
        return jsonify({
            "status": "ERROR",
            "message": "An internal system error occurred during review execution.",
            "code": 500
        }), 500
