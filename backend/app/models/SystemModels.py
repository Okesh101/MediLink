# app/models/SystemModels.py

from app import db
from app.utils.db_types import GUID
from app.utils.time import lagos_now, to_lagos_iso
import uuid


class TimelineEvent(db.Model):
    __tablename__ = 'timeline_events'

    id = db.Column(GUID(), primary_key=True,
                   default=uuid.uuid4, nullable=False)
    patient_public_id = db.Column(
        db.String(12),
        db.ForeignKey('patients.public_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    # 'AI_CHAT', 'DISCHARGE', 'FOLLOW_UP', 'RECORD_ADDED'
    event_type = db.Column(db.String(50), nullable=False)

    created_at = db.Column(db.DateTime(
        timezone=True), default=lagos_now, server_default=db.func.now(), index=True)

    patient = db.relationship(
        'Patient', backref=db.backref('timeline', lazy='dynamic'))

    def to_dict(self):
        return {
            "id": str(self.id),
            "title": self.title,
            "description": self.description,
            "event_type": self.event_type,
            "created_at": to_lagos_iso(self.created_at)
        }
