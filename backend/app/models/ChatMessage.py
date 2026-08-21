# app/models/ChatMessage.py

from app import db
from app.utils.db_types import GUID
from app.utils.time import lagos_now, to_lagos_iso
import uuid


class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'

    id = db.Column(GUID(), primary_key=True,
                   default=uuid.uuid4, nullable=False)
    patient_public_id = db.Column(
        db.String(12),
        db.ForeignKey('patients.public_id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    # 'user', 'assistant', 'system', 'tool'
    role = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lagos_now,
        server_default=db.func.now(),
        index=True
    )

    patient = db.relationship(
        'Patient', backref=db.backref('chat_history', lazy='dynamic'))

    def to_dict(self):
        return {
            "id": str(self.id),
            "role": self.role,
            "content": self.content,
            "created_at": to_lagos_iso(self.created_at)
        }
