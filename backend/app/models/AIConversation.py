# app/models/AIConversation.py

from app import db
from app.utils.db_types import GUID
from app.utils.time import lagos_now, to_lagos_iso
import uuid


class AIConversation(db.Model):
    __tablename__ = 'ai_conversations'

    id = db.Column(GUID(), primary_key=True,
                   default=uuid.uuid4, nullable=False)
    patient_public_id = db.Column(
        db.String(12),
        db.ForeignKey('patients.public_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    status = db.Column(db.String(20), default='active',
                       nullable=False)  # 'active', 'completed'
    # Generated Doctor Summary
    symptom_summary = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime(timezone=True),
                           default=lagos_now, server_default=db.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), default=lagos_now,
                           onupdate=lagos_now, server_default=db.func.now())

    messages = db.relationship(
        'ChatMessage', backref='conversation', cascade='all, delete-orphan', lazy='selectin')
    patient = db.relationship('Patient', backref=db.backref(
        'ai_conversations', lazy='dynamic'))

    def to_dict(self):
        return {
            "id": str(self.id),
            "patient_public_id": self.patient_public_id,
            "status": self.status,
            "symptom_summary": self.symptom_summary,
            "created_at": to_lagos_iso(self.created_at),
            "messages": [m.to_dict() for m in self.messages]
        }

