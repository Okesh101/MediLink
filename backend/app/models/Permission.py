# app/models/Permission.py

from app import db

class Permission(db.Model):
    __tablename__ = "permissions"
    id = db.Column(db.Integer, primary_key=True, unique=True,
                   nullable=False, autoincrement=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
