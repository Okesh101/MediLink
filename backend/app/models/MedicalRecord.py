from app import db
from app.utils.db_types import GUID
from app.utils.time import lagos_now, to_lagos_iso
import uuid


class MedicalRecord(db.Model):
    __tablename__ = 'medical_records'

    id = db.Column(GUID(), primary_key=True,
                   default=uuid.uuid4, nullable=False)
    hospital_id = db.Column(GUID(), db.ForeignKey(
        'hospitals.id', ondelete='CASCADE'), nullable=False, index=True)
    doctor_id = db.Column(GUID(), db.ForeignKey(
        'staff.id', ondelete='CASCADE'), nullable=False, index=True)

    # Must match Patient.public_id (20)
    patient_public_id = db.Column(
        db.String(12),
        db.ForeignKey('patients.public_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    chief_complaint = db.Column(db.Text, nullable=True)
    diagnosis = db.Column(db.Text, nullable=False)
    doctor_notes = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime(timezone=True),
                           default=lagos_now, server_default=db.func.now())

    documents = db.relationship(
        'RecordDocuments', backref='medical_record', cascade='all, delete-orphan', lazy='selectin')

    # Explicit unique backrefs
    hospital = db.relationship('Hospital', backref=db.backref(
        'hospital_medical_records', lazy='selectin'))
    doctor = db.relationship('Staff', backref=db.backref(
        'authored_medical_records', lazy='selectin'))
    patient = db.relationship('Patient', foreign_keys=[
                              patient_public_id], backref=db.backref('patient_medical_records', lazy='selectin'))

    def to_dict(self):
        return {
            "id": str(self.id),
            "hospital_id": str(self.hospital_id),
            "hospital_name": self.hospital.name if self.hospital else None,
            "doctor_id": str(self.doctor_id),
            "doctor_name": self.doctor.name if self.doctor else None,
            "patient_public_id": self.patient_public_id,
            "chief_complaint": self.chief_complaint,
            "diagnosis": self.diagnosis,
            "doctor_notes": self.doctor_notes,
            "documents": [doc.to_dict() for doc in self.documents] if self.documents else [],
            "created_at": to_lagos_iso(self.created_at),
        }
