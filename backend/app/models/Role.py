# app/models/Role.py

from app import db
from app.utils.db_types import GUID


role_permissions = db.Table(
    "role_permissions",
    db.Column('role_id', db.Integer, db.ForeignKey(
        'roles.id', ondelete="CASCADE"), primary_key=True, nullable=False),
    db.Column('permission_id', db.Integer, db.ForeignKey(
        'permissions.id', ondelete="CASCADE"), primary_key=True, nullable=False),
)

actor_roles = db.Table(
    'actor_roles',
    db.Column(
        'actor_id',
        GUID(),
        primary_key=True,
        nullable=False
    ),
    db.Column(
        'actor_type',
        db.String(20),
        primary_key=True,
        nullable=False
    ),  # 'staff', 'patient', 'hospital_admin'
    db.Column(
        'role_id',
        db.Integer,
        db.ForeignKey('roles.id', ondelete='CASCADE'),
        primary_key=True,
        nullable=False
    )
)


class Role(db.Model):
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True, unique=True,
                   nullable=False, autoincrement=True)
    # eg. 'Doctor', 'Nurse', 'Hospital Admin', 'Patient', etc.
    name = db.Column(db.Text, unique=True, nullable=False)

    permissions = db.relationship(
        "Permission",
        secondary=role_permissions,
        backref=db.backref("roles", lazy="dynamic"),
        lazy='subquery'
    )

    def __repr__(self):
        return f"<Role: {self.name}>"
