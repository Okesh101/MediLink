# app/models/Patient.py

from app import db
from app.models.Role import actor_roles, Role
from app.utils.types import Sex
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import event, and_
import uuid
import hashlib
from zoneinfo import ZoneInfo


SEX_CHOICES = ", ".join(
    f"'{sex.value}'" for sex in Sex)


class Patient(db.Model):
    __tablename__ = 'patients'

    __table_args__ = (
        db.CheckConstraint(
            f"sex IN ({SEX_CHOICES})",
            name="valid_sex_status"
        ),
    )

    # Configure ID as a true UUID string type
    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=db.text("gen_random_uuid()"),
        nullable=False
    )
    public_id = db.Column(db.String(12), unique=True,
                          nullable=False, index=True)
    
    firstname = db.Column(db.String(100), nullable=False)
    lastname = db.Column(db.String(100), nullable=False)
    sex = db.Column(db.String(10), nullable=False)
    phone = db.Column(db.String(11), nullable=False, unique=True, index=True)
    dob = db.Column(db.Date, nullable=False)
    nin = db.Column(db.String(11), nullable=False, unique=True)

    email = db.Column(db.String(150), nullable=True, unique=True)

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

    # Polymorphic Relationship for Patient roles
    roles = db.relationship(
        "Role",
        secondary=actor_roles,
        primaryjoin=and_(
            id == actor_roles.c.actor_id,
            actor_roles.c.actor_type == "patient"
        ),
        secondaryjoin=Role.id == actor_roles.c.role_id,
        lazy="selectin",
        overlaps="roles,hospitals,staff_members"
    )

    # Helper method to set hashed password
    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)

    # Helper method to verify password during login
    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)

    def assign_role(self, role):
        db.session.execute(
            actor_roles.insert().values(
                actor_id=self.id,
                actor_type='patient',
                role_id=role.id
            )
        )

    def to_dict(self):
        created_at_iso = None
        if self.created_at:
            tz = ZoneInfo("Africa/Lagos")
            created_at_iso = (self.created_at if self.created_at.tzinfo else self.created_at.replace(
                tzinfo=tz)).astimezone(tz).isoformat()

        return {
            "id": str(self.id),
            "firstname": self.firstname,
            "lastname": self.lastname,
            "sex": self.sex,
            "phone": self.phone,
            "public_id": self.public_id,
            "dob": self.dob.strftime('%Y-%m-%d') if self.dob else None,
            "roles": [r.name for r in self.roles],
            "created_at": created_at_iso
        }


@event.listens_for(Patient, 'before_insert')
def receive_before_insert(mapper, connection, target):
    if not target.id:
        target.id = uuid.uuid4()

    # ONLY UPPERCASE for voice clarity (makes it easier to read over the phone)
    alphabet = "23456789BCDGHIJKLMNPQRSTUVWY"
    base = len(alphabet)

    uuid_bytes = target.id.hex.encode('utf-8')
    hash_pool = hashlib.sha256(uuid_bytes).digest()

    # Generate 10 clean uppercase characters
    raw_chars = []
    for i in range(10):
        byte_value = hash_pool[i]
        raw_chars.append(alphabet[byte_value % base])

    # Chunk them: Split into groups of 3, 3, and 4
    # Example: ['B','C','4','D','G','7','M','N','9','Z'] -> "BC4-DG7-MN9Z"
    chunked_id = f"{''.join(raw_chars[0:3])}-{''.join(raw_chars[3:6])}-{''.join(raw_chars[6:10])}"

    target.public_id = chunked_id
