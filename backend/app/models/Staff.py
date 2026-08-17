# app/models/Staff.py

from app import db
from app.models.Role import actor_roles, Role
from app.utils.types import Sex
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import and_
import uuid
from zoneinfo import ZoneInfo


SEX_CHOICES = ", ".join(
    f"'{sex.value}'" for sex in Sex)


class Staff(db.Model):
    __tablename__ = 'staff'

    __table_args__ = (
        db.CheckConstraint(
            f"sex IN ({SEX_CHOICES})",
            name="valid_sex_status"
        ),
    )

    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=db.text("gen_random_uuid()"),
        nullable=False
    )
    hospital_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey('hospitals.id', ondelete='CASCADE'),
        nullable=False  # Removed unique=True so a hospital can have multiple staff
    )
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True, index=True)
    sex = db.Column(db.String(10), nullable=False)
    phone = db.Column(db.String(11), nullable=False, unique=True)
    nin = db.Column(db.String(11), nullable=False, unique=True)
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

    # Direct 1-to-Many back to Hospital
    hospital = db.relationship(
        'Hospital',
        backref=db.backref('staff_members', lazy='selectin')
    )

    # Polymorphic Relationship to Role via actor_roles
    roles = db.relationship(
        "Role",
        secondary=actor_roles,
        primaryjoin=and_(
            id == actor_roles.c.actor_id,
            actor_roles.c.actor_type == "staff"
        ),
        secondaryjoin=Role.id == actor_roles.c.role_id,
        lazy="selectin",
        overlaps="roles,hospitals,patients"
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
                actor_type="staff",
                role_id=role.id
            )
        )

    def has_role(self, role_name):
        return any(role.name == role_name for role in self.roles)

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
            "hospital_id": str(self.hospital_id),
            "name": self.name,
            "email": self.email,
            "sex": self.sex,
            "phone": self.phone,
            "roles": [r.name for r in self.roles],
            "created_at": created_at_iso,
            "updated_at": updated_at_iso
        }
