# app/models/RecordDocuments.py

from app import db
from sqlalchemy.dialects.postgresql import UUID
from zoneinfo import ZoneInfo


class RequestDocuments(db.Model):
    __tablename__ = 'record_documents'

    id = db.Column(
        db.Integer, primary_key=True, unique=True,
        nullable=False, autoincrement=True
    )
    record_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey('medical_records.id', ondelete='CASCADE'),
        nullable=False
    )
    title = db.Column(db.String(255), nullable=False)
    doc_url = db.Column(db.Text, nullable=False)

    uploaded_at = db.Column(
        db.DateTime(timezone=True),
        server_default=db.text("TIMEZONE('Africa/Lagos', NOW())")
    )

    updated_at = db.Column(
        db.DateTime(timezone=True),
        server_default=db.text("TIMEZONE('Africa/Lagos', NOW())"),
        onupdate=db.text("TIMEZONE('Africa/Lagos', NOW())")
    )

    def to_dict(self):
        uploaded_at_iso = None
        if self.uploaded_at:
            tz = ZoneInfo("Africa/Lagos")
            uploaded_at_iso = (self.uploaded_at if self.uploaded_at.tzinfo else self.uploaded_at.replace(
                tzinfo=tz)).astimezone(tz).isoformat()

        return {
            "id": str(self.id),
            "record_id": str(self.record_id),
            "title": self.title,
            "doc_url": self.doc_url,
            "uploaded_at": uploaded_at_iso
        }
