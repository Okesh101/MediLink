from app import db
from app.models.Role import actor_roles, Role
from app.utils.types import Sex
from app.utils.db_types import GUID
from app.utils.time import lagos_now, to_lagos_iso
from sqlalchemy import and_
import uuid

SEX_CHOICES = ", ".join(f"'{sex.value}'" for sex in Sex)


class Staff(db.Model):
    __tablename__ = 'staff'

    __table_args__ = (
        db.CheckConstraint(f"sex IN ({SEX_CHOICES})", name="valid_sex_status"),
    )

    id = db.Column(GUID(), primary_key=True,
                   default=uuid.uuid4, nullable=False)
    hospital_id = db.Column(GUID(), db.ForeignKey(
        'hospitals.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    specialty = db.Column(db.String(100), nullable=True,
                          index=True)  # <-- REQUIRED FOR AI SEARCH
    email = db.Column(db.String(120), nullable=False, unique=True, index=True)
    sex = db.Column(db.String(10), nullable=False)
    phone = db.Column(db.String(11), nullable=False, unique=True)
    nin = db.Column(db.String(11), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)

    created_at = db.Column(db.DateTime(timezone=True),
                           default=lagos_now, server_default=db.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), default=lagos_now,
                           onupdate=lagos_now, server_default=db.func.now())

    hospital = db.relationship('Hospital', backref=db.backref(
        'staff_members', lazy='selectin'))

    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)

    roles = db.relationship(
        "Role",
        secondary=actor_roles,
        primaryjoin=and_(id == actor_roles.c.actor_id,
                         actor_roles.c.actor_type == "staff"),
        secondaryjoin=Role.id == actor_roles.c.role_id,
        lazy="selectin",
        overlaps="roles"
    )

    def to_dict(self):
        return {
            "id": str(self.id),
            "hospital_id": str(self.hospital_id),
            "hospital_name": self.hospital.name if self.hospital else None,
            "name": self.name,
            "specialty": self.specialty,
            "email": self.email,
            "sex": self.sex,
            "phone": self.phone,
            "roles": [r.name for r in self.roles],
            "created_at": to_lagos_iso(self.created_at)
        }
