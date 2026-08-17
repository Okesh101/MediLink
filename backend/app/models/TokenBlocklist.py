# app/models/TokenBlocklist.py

from app import db

class TokenBlocklist(db.Model):
    __tablename__ = 'token_blocklist'

    id = db.Column(db.Integer, primary_key=True,
                   nullable=False, autoincrement=True)
    jti = db.Column(db.String(36),
                    nullable=False,
                    index=True)  # Unique identifier
    created_at = db.Column(db.DateTime(timezone=True),
                           nullable=False,
                           server_default=db.text(
                               "TIMEZONE('Africa/Lagos', NOW())")
                           )
