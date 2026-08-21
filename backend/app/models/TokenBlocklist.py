# app/models/TokenBlocklist.py

from app import db
from app.utils.time import lagos_now


class TokenBlocklist(db.Model):
    __tablename__ = 'token_blocklist'

    id = db.Column(db.Integer, primary_key=True,
                   nullable=False, autoincrement=True)
    jti = db.Column(db.String(36),
                    nullable=False,
                    index=True)
    created_at = db.Column(db.DateTime(timezone=True),
                           nullable=False,
                           default=lagos_now,
                           server_default=db.func.now()
                           )
