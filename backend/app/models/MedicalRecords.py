# app/models/MedicalRecord.py

from app import db
from sqlalchemy.dialects.postgresql import UUID
import uuid
from zoneinfo import ZoneInfo


class MedicalRecord(db.Model):
    __tablename__ = 'medical_records'

    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=db.text("gen_random_uuid()"),
        nullable=False
    )
    hospital_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey('hospitals.id', ondelete='CASCADE'),
        nullable=False
    )
    doctor_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey('staff.id', ondelete='CASCADE'),
        nullable=False
    )
    patient_public_id = db.Column(
        db.String(12),
        db.ForeignKey('patients.public_id', ondelete='CASCADE'),
        nullable=False
    )
    diagnosis = db.Column(db.Text, nullable=False)
    doctor_notes = db.Column(db.Text, nullable=True)

    created_at = db.Column(
        db.DateTime(timezone=True),
        server_default=db.text("TIMEZONE('Africa/Lagos', NOW())")
    )

    # Direct 1-to-Many back to Documents
    documents = db.relationship(
        'RecordDocuments',
        backref='medical_record',
        cascade='all, delete-orphan',
        lazy='selectin'
    )

    def to_dict(self):
        created_at_iso = None
        if self.created_at:
            tz = ZoneInfo("Africa/Lagos")
            created_at_iso = (self.created_at if self.created_at.tzinfo else self.created_at.replace(
                tzinfo=tz)).astimezone(tz).isoformat()

        return {
            "id": str(self.id),
            "hospital_id": str(self.hospital_id),
            "doctor_id": str(self.doctor_id),
            "patient_public_id": self.patient_public_id,
            "diagnosis": self.diagnosis,
            "doctor_notes": self.doctor_notes,
            "record_docs": [doc.to_dict() for doc in self.documents] if self.documents else None,
            "created_at": created_at_iso,
        }
