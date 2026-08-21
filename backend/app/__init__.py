# app/__init__.py

from flask import Flask, jsonify
from redis import Redis
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_limiter.errors import RateLimitExceeded
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from sqlalchemy.exc import IntegrityError
from sqlalchemy import event

from app.config.config import DevelopmentConfig, ProductionConfig, TestingConfig
from werkzeug.exceptions import MethodNotAllowed, NotFound
from app.services.cloudinary.cloudinary import init_cloudinary

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
import os
import pytz
import atexit
import logging


db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=['200 per day', '50 per hour']
)
redis_client = None
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler(
    executors={'default': ThreadPoolExecutor(5)},
    job_defaults={'coalesce': True, 'max_instances': 1},
    timezone=pytz.timezone("Africa/Lagos")
)


def create_app(config_object=None):
    app = Flask(__name__)

    if config_object is not None:
        app.config.from_object(config_object)
    else:
        env = os.getenv('FLASK_ENV', 'development')
        if env == 'production':
            app.config.from_object(ProductionConfig)
        elif env == 'testing':
            app.config.from_object(TestingConfig)
        else:
            app.config.from_object(DevelopmentConfig)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    limiter.init_app(app)
    init_cloudinary(app)

    global redis_client
    if app.config.get("TESTING"):
        redis_client = None
    elif app.config.get("REDIS_URL"):
        redis_client = Redis.from_url(
            app.config['REDIS_URL'],
            decode_responses=True
        )
    else:
        redis_client = None

    with app.app_context():
        if str(app.config.get("SQLALCHEMY_DATABASE_URI") or "").startswith("sqlite"):
            event.listen(db.engine, "connect", _set_sqlite_pragma)

    # Force load models into the application context for migrations
    from app.models.TokenBlocklist import TokenBlocklist
    from app.models.Patient import Patient
    from app.models.Hospital import Hospital
    from app.models.Staff import Staff
    from app.models.Role import Role, actor_roles, role_permissions
    from app.models.Permission import Permission
    from app.models.MedicalRecord import MedicalRecord
    from app.models.RecordDocuments import RecordDocuments
    from app.models.Access import Requests, AccessGrants

    # Blueprints
    from app.api.health.routes import health_bp
    from app.api.auth.patient.routes import auth_patient_bp
    from app.api.auth.hospital.routes import auth_hospital_bp
    from app.api.auth.staff.routes import auth_staff_bp
    from app.api.patient.routes import patient_bp
    from app.api.staff.routes import staff_bp
    from app.api.records.routes import records_bp
    from app.api.access.routes import access_bp

    app.register_blueprint(health_bp, url_prefix='/api/v1/health')
    app.register_blueprint(auth_patient_bp, url_prefix='/api/v1/auth/patient')
    app.register_blueprint(
        auth_hospital_bp, url_prefix='/api/v1/auth/hospital')
    app.register_blueprint(auth_staff_bp, url_prefix='/api/v1/auth/staff')
    app.register_blueprint(patient_bp, url_prefix='/api/v1/patient')
    app.register_blueprint(staff_bp, url_prefix="/api/v1/staff")
    app.register_blueprint(records_bp, url_prefix="/api/v1/records")
    app.register_blueprint(access_bp, url_prefix="/api/v1/access")

    @app.cli.command("seed-permissions")
    def seed_permissions_command():
        """Flask CLI integration hook to safely force populate database rules."""
        logger.info("Booting core system database permissions synchronizer...")
        with app.app_context():
            seed_system_permissions_and_roles()
        logger.info("Permissions synchronization complete.")

    if (
        not app.config.get("TESTING")
        and (not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true")
    ):
        from app.services.scheduler.apscheduler import continuous_ping

        scheduler.add_job(
            id='ping_server',
            func=continuous_ping,
            trigger='interval',
            minutes=10,
            replace_existing=True
        )

        if not scheduler.running:
            scheduler.start()
            atexit.register(lambda: scheduler.shutdown())
            logger.info("Scheduler started with Africa/Lagos time tracking.")
        else:
            logger.warning(
                "Scheduler already active, skipping initialization.")

    @app.errorhandler(RateLimitExceeded)
    def handle_rate_limit_exceeded(e):
        return jsonify({
            "status": "ERROR",
            "code": 429,
            "message": f"Rate Limit Exceeded! Slow down. Allowed limit: {e.description}."
        }), 429

    @app.errorhandler(MethodNotAllowed)
    def handle_method_not_allowed(e):
        return jsonify({
            "status": "ERROR",
            "code": 405,
            "message": "The HTTP method used is not allowed for this endpoint."
        }), 405

    @app.errorhandler(NotFound)
    def handle_not_found(e):
        return jsonify({
            "status": "ERROR",
            "code": 404,
            "message": "The requested URL or resource was not found on this server."
        }), 404

    @app.errorhandler(IntegrityError)
    def handle_integrity_error(error):
        db.session.rollback()
        logger.info("INTEGRITY ERROR: %s", error)
        return jsonify({
            "status": "ERROR",
            "code": 409,
            "message": "A record duplicate conflict occurred."
        }), 409

    return app


def _set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    from app.models.TokenBlocklist import TokenBlocklist
    jti = jwt_payload["jti"]

    token = db.session.execute(
        db.select(TokenBlocklist).filter_by(jti=jti)
    ).scalar_one_or_none()

    return token is not None


def seed_system_permissions_and_roles():
    """Idempotently populates core permissions and maps them to default roles."""
    from app.models.Permission import Permission
    from app.models.Role import Role

    system_permissions = [
        "patient:manage_profile",
        "staff:manage_profile",
        "hospital:manage_profile",
        "hospital:manage_staff",
        "hospital:view_staff",
        "hospital:manage_roles",
        "hospital:view_analytics",
        "patient:lookup",
        "access:request",
        "access:review",
        "access:view_requests",
        "access:revoke",
        "medical_record:read",
        "medical_record:write",
        "medical_record:view_own",
        "lab:upload_results",
        "lab:view_results",
    ]
    hospital_admin_allowed = [
        "hospital:manage_profile",
        "hospital:manage_staff",
        "hospital:view_staff",
        "hospital:manage_roles",
        "hospital:view_analytics",
    ]
    doctor_allowed = [
        "staff:manage_profile",
        "patient:lookup",
        "access:request",
        "access:view_requests",
        "medical_record:read",
        "medical_record:write",
        "lab:upload_results",
        "lab:view_results",
    ]
    patient_allowed = [
        "patient:manage_profile",
        "access:review",
        "access:view_requests",
        "access:revoke",
        "medical_record:view_own",
    ]

    try:
        permission_objects = {}
        for perm_name in system_permissions:
            perm = db.session.execute(db.select(Permission).filter_by(
                name=perm_name)).scalar_one_or_none()
            if not perm:
                perm = Permission(name=perm_name)
                db.session.add(perm)
                logger.info("Created system permission: '%s'", perm_name)
            permission_objects[perm_name] = perm

        db.session.flush()

        def get_or_create_role(role_name):
            role = db.session.execute(
                db.select(Role).filter_by(name=role_name)
            ).scalar_one_or_none()
            if not role:
                role = Role(name=role_name)
                db.session.add(role)
            return role

        super_admin_role = get_or_create_role("Super Admin")
        hospital_admin_role = get_or_create_role("Hospital Admin")
        doctor_role = get_or_create_role("Doctor")
        patient_role = get_or_create_role("Patient")

        db.session.flush()

        role_mappings = [
            (hospital_admin_role, hospital_admin_allowed),
            (doctor_role, doctor_allowed),
            (patient_role, patient_allowed),
        ]

        for role_obj, allowed_perms in role_mappings:
            for perm_name in allowed_perms:
                target_perm = permission_objects[perm_name]
                if target_perm not in role_obj.permissions:
                    role_obj.permissions.append(target_perm)

        for target_perm in permission_objects.values():
            if target_perm not in super_admin_role.permissions:
                super_admin_role.permissions.append(target_perm)

        db.session.commit()
        logger.info(
            "Permissions and Role configurations successfully synchronized.")

    except Exception as e:
        db.session.rollback()
        logger.error("Error occurred while seeding permissions: %s", str(e))
        print("Warning: Auto-seeding permissions failed! Check logs for details.")
