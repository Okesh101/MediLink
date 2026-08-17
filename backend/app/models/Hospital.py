# app/models/Hospital.py

from app import db
from app.models.Role import actor_roles, Role
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import and_
import uuid
from zoneinfo import ZoneInfo


class Hospital(db.Model):
    __tablename__ = 'hospitals'

    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=db.text("gen_random_uuid()"),
        nullable=False
    )
    reg_no = db.Column(db.String(100), unique=True, nullable=False, index=True)
    name = db.Column(db.Text, nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True, index=True)
    phone = db.Column(db.String(11), nullable=False, unique=True)
    address = db.Column(db.Text, nullable=False)
    is_verified = db.Column(db.Boolean, nullable=False,
                            default=False, server_default=db.text("FALSE"))
    password_hash = db.Column(db.String(255), nullable=False)

    created_at = db.Column(
        db.DateTime(timezone=True),
        server_default=db.text("TIMEZONE('Africa/Lagos', NOW())")
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        server_default=db.text("TIMEZONE('Africa/Lagos', NOW())"),
        onupdate=db.text("TIMEZONE('Africa/Lagos', NOW())")
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
        created_at_iso = None
        if self.created_at:
            tz = ZoneInfo("Africa/Lagos")
            created_at_iso = (self.created_at if self.created_at.tzinfo else self.created_at.replace(
                tzinfo=tz)).astimezone(tz).isoformat()

        updated_at_iso = None
        if self.updated_at:
            tz = ZoneInfo("Africa/Lagos")
            updated_at_iso = (self.updated_at if self.updated_at.tzinfo else self.updated_at.replace(
                tzinfo=tz)).astimezone(tz).isoformat()

        return {
            "id": str(self.id),
            "reg_no": self.reg_no,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "address": self.address,
            "is_verified": self.is_verified,
            "roles": [r.name for r in self.roles],
            "created_at": created_at_iso,
            "updated_at": updated_at_iso
        }
