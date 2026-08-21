# app/models/Access.py

from app import db
from app.utils.db_types import GUID
from app.utils.types import GrantStatus, RequestStatus, AccessScope
from app.utils.time import lagos_now, to_lagos_iso
import uuid

GRANT_CHOICES = ", ".join(
    f"'{status.value}'" for status in GrantStatus)

REQUEST_STATUS_CHOICES = ", ".join(
    f"'{status.value}'" for status in RequestStatus)


class Requests(db.Model):
    __tablename__ = 'access_requests'

    __table_args__ = (
        db.CheckConstraint(
            f"status IN ({REQUEST_STATUS_CHOICES})",
            name="valid_request_status"
        ),
    )

    id = db.Column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )
    patient_public_id = db.Column(
        db.String(12),
        db.ForeignKey('patients.public_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    staff_id = db.Column(
        GUID(),
        db.ForeignKey('staff.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    hospital_id = db.Column(
        GUID(),
        db.ForeignKey('hospitals.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    reason = db.Column(db.Text, nullable=True)
    scope = db.Column(
        db.String(100),
        nullable=False,
        default=AccessScope.VIEW_AND_CREATE_RECORDS.value
    )
    status = db.Column(
        db.String(20),
        nullable=False,
        default=RequestStatus.PENDING.value
    )
    reviewed_at = db.Column(db.DateTime(timezone=True), nullable=True)

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lagos_now,
        server_default=db.func.now()
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lagos_now,
        onupdate=lagos_now,
        server_default=db.func.now()
    )

    staff = db.relationship(
        'Staff',
        backref=db.backref('access_requests', lazy='selectin')
    )
    hospital = db.relationship(
        'Hospital',
        backref=db.backref('access_requests', lazy='selectin')
    )
    patient = db.relationship(
        'Patient',
        foreign_keys=[patient_public_id],
        backref=db.backref('access_requests', lazy='selectin')
    )
    grant = db.relationship(
        'AccessGrants',
        backref='request',
        uselist=False,
        cascade='all, delete-orphan'
    )

    def to_dict(self):
        return {
            "id": str(self.id),
            "patient_public_id": self.patient_public_id,
            "staff_id": str(self.staff_id),
            "staff_name": self.staff.name if self.staff else None,
            "hospital_id": str(self.hospital_id),
            "hospital_name": self.hospital.name if self.hospital else None,
            "reason": self.reason,
            "scope": self.scope,
            "status": self.status,
            "reviewed_at": to_lagos_iso(self.reviewed_at),
            "created_at": to_lagos_iso(self.created_at),
            "updated_at": to_lagos_iso(self.updated_at)
        }


class AccessGrants(db.Model):
    __tablename__ = 'access_grants'

    __table_args__ = (
        db.CheckConstraint(
            f"status IN ({GRANT_CHOICES})",
            name="valid_grant_status"
        ),
    )

    id = db.Column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )
    request_id = db.Column(
        GUID(),
        db.ForeignKey('access_requests.id', ondelete='CASCADE'),
        nullable=False,
        unique=True
    )
    patient_public_id = db.Column(
        db.String(12),
        db.ForeignKey('patients.public_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    staff_id = db.Column(
        GUID(),
        db.ForeignKey('staff.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    hospital_id = db.Column(
        GUID(),
        db.ForeignKey('hospitals.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    scope = db.Column(
        db.String(100),
        nullable=False,
        default=AccessScope.VIEW_AND_CREATE_RECORDS.value
    )
    status = db.Column(
        db.String(20),
        nullable=False,
        default=GrantStatus.GRANTED.value
    )
    expires_at = db.Column(db.DateTime(timezone=True), nullable=True)

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lagos_now,
        server_default=db.func.now()
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lagos_now,
        onupdate=lagos_now,
        server_default=db.func.now()
    )

    staff = db.relationship(
        'Staff',
        backref=db.backref('access_grants', lazy='selectin')
    )
    hospital = db.relationship(
        'Hospital',
        backref=db.backref('access_grants', lazy='selectin')
    )
    patient = db.relationship(
        'Patient',
        foreign_keys=[patient_public_id],
        backref=db.backref('access_grants', lazy='selectin')
    )

    def to_dict(self):
        return {
            "id": str(self.id),
            "request_id": str(self.request_id),
            "patient_public_id": self.patient_public_id,
            "staff_id": str(self.staff_id),
            "staff_name": self.staff.name if self.staff else None,
            "hospital_id": str(self.hospital_id),
            "hospital_name": self.hospital.name if self.hospital else None,
            "scope": self.scope,
            "status": self.status,
            "expires_at": to_lagos_iso(self.expires_at),
            "created_at": to_lagos_iso(self.created_at),
            "updated_at": to_lagos_iso(self.updated_at)
        }
