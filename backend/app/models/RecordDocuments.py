# app/models/RecordDocuments.py

from app import db
from app.utils.db_types import GUID
from app.utils.time import lagos_now, to_lagos_iso


class RecordDocuments(db.Model):
    __tablename__ = 'record_documents'

    id = db.Column(
        db.Integer, primary_key=True, unique=True,
        nullable=False, autoincrement=True
    )
    record_id = db.Column(
        GUID(),
        db.ForeignKey('medical_records.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    title = db.Column(db.String(255), nullable=False)
    doc_url = db.Column(db.Text, nullable=False)

    uploaded_at = db.Column(
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

    def to_dict(self):
        return {
            "id": self.id,
            "record_id": str(self.record_id),
            "title": self.title,
            "doc_url": self.doc_url,
            "uploaded_at": to_lagos_iso(self.uploaded_at)
        }
