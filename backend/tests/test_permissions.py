# tests/test_permissions.py

from app import db, seed_system_permissions_and_roles
from app.models.Permission import Permission
from app.models.Role import Role


def test_seeded_roles_have_expected_permissions(app):
    with app.app_context():
        seed_system_permissions_and_roles()

        doctor = db.session.execute(
            db.select(Role).filter_by(name="Doctor")
        ).scalar_one()
        patient = db.session.execute(
            db.select(Role).filter_by(name="Patient")
        ).scalar_one()
        hospital = db.session.execute(
            db.select(Role).filter_by(name="Hospital Admin")
        ).scalar_one()
        super_admin = db.session.execute(
            db.select(Role).filter_by(name="Super Admin")
        ).scalar_one()

        doctor_perms = {perm.name for perm in doctor.permissions}
        patient_perms = {perm.name for perm in patient.permissions}
        hospital_perms = {perm.name for perm in hospital.permissions}
        super_perms = {perm.name for perm in super_admin.permissions}

        assert "medical_record:read" in doctor_perms
        assert "medical_record:write" in doctor_perms
        assert "access:request" in doctor_perms
        assert "patient:lookup" in doctor_perms
        assert "access:review" not in doctor_perms
        assert "hospital:manage_staff" not in doctor_perms

        assert "access:review" in patient_perms
        assert "access:revoke" in patient_perms
        assert "medical_record:view_own" in patient_perms
        assert "medical_record:write" not in patient_perms
        assert "access:request" not in patient_perms

        assert "hospital:manage_staff" in hospital_perms
        assert "hospital:view_staff" in hospital_perms
        assert "medical_record:read" not in hospital_perms
        assert "access:request" not in hospital_perms

        all_permission_names = {
            perm.name for perm in db.session.scalars(db.select(Permission)).all()
        }
        assert super_perms == all_permission_names


def test_seed_permissions_is_idempotent(app):
    with app.app_context():
        seed_system_permissions_and_roles()
        first_count = db.session.scalar(db.select(db.func.count(Permission.id)))
        seed_system_permissions_and_roles()
        second_count = db.session.scalar(db.select(db.func.count(Permission.id)))
        assert first_count == second_count
        assert first_count >= 15
