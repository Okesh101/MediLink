# app/models/Hospital.py

from app import db
from app.models.Role import actor_roles, Role
from app.utils.db_types import GUID
from app.utils.time import lagos_now, to_lagos_iso
from sqlalchemy import and_
import uuid


class Hospital(db.Model):
    __tablename__ = 'hospitals'

    id = db.Column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )
    reg_no = db.Column(db.String(100), unique=True, nullable=False, index=True)
    name = db.Column(db.Text, nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True, index=True)
    phone = db.Column(db.String(11), nullable=False, unique=True)
    address = db.Column(db.Text, nullable=False)
    is_verified = db.Column(db.Boolean, nullable=False, default=False)
    password_hash = db.Column(db.String(255), nullable=False)

    created_at = db.Column(
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

    # Polymorphic Relationship for Hospital Admin roles
    roles = db.relationship(
        "Role",
        secondary=actor_roles,
        primaryjoin=and_(
            id == actor_roles.c.actor_id,
            actor_roles.c.actor_type == "hospital_admin"
        ),
        secondaryjoin=Role.id == actor_roles.c.role_id,
        lazy="selectin",
        overlaps="roles,patients,staff_members"
    )

    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)

    def assign_role(self, role):
        db.session.execute(
            actor_roles.insert().values(
                actor_id=self.id,
                actor_type="hospital_admin",
                role_id=role.id
            )
        )

    def to_dict(self):
        return {
            "id": str(self.id),
            "reg_no": self.reg_no,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "address": self.address,
            "is_verified": self.is_verified,
            "roles": [r.name for r in self.roles],
            "created_at": to_lagos_iso(self.created_at),
            "updated_at": to_lagos_iso(self.updated_at)
        }
