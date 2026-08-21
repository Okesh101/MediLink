# app/utils/helpers.py

import uuid
from sqlalchemy import func

from app import db
from app.utils.time import lagos_now
from app.utils.types import GrantStatus, RequestStatus


def as_uuid(value):
    if value is None:
        return None
    if isinstance(value, uuid.UUID):
        return value
    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError, AttributeError):
        return None


def normalize_public_id(value):
    if not value:
        return ""
    return str(value).strip().replace("-", "").upper()


def find_patient_by_public_id(public_id):
    from app.models.Patient import Patient

    cleaned = normalize_public_id(public_id)
    if not cleaned:
        return None

    return db.session.scalar(
        db.select(Patient).where(
            func.replace(Patient.public_id, "-", "") == cleaned
        )
    )


def get_pending_request(staff_id, patient_public_id):
    from app.models.Access import Requests

    return db.session.scalar(
        db.select(Requests).where(
            Requests.staff_id == staff_id,
            Requests.patient_public_id == patient_public_id,
            Requests.status == RequestStatus.PENDING.value,
        )
    )


def get_active_grant(staff_id, patient_public_id):
    from app.models.Access import AccessGrants

    now = lagos_now()
    grants = db.session.scalars(
        db.select(AccessGrants)
        .where(
            AccessGrants.staff_id == staff_id,
            AccessGrants.patient_public_id == patient_public_id,
            AccessGrants.status == GrantStatus.GRANTED.value,
        )
        .order_by(AccessGrants.created_at.desc())
    ).all()

    for grant in grants:
        if grant.expires_at is None:
            return grant
        expires_at = grant.expires_at
        if expires_at.tzinfo is None:
            from app.utils.time import LAGOS_TZ
            expires_at = expires_at.replace(tzinfo=LAGOS_TZ)
        if expires_at > now:
            return grant

        grant.status = GrantStatus.EXPIRED.value

    if grants:
        db.session.commit()
    return None


def has_active_grant(staff_id, patient_public_id):
    return get_active_grant(staff_id, patient_public_id) is not None
