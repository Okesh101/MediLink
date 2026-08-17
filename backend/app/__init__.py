# app/__init__.py

from flask import Flask, jsonify
from redis import Redis
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_limiter.errors import RateLimitExceeded
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager  # Import it
from sqlalchemy.exc import IntegrityError

from app.config.config import DevelopmentConfig, ProductionConfig  # Import the class
from werkzeug.exceptions import MethodNotAllowed, NotFound
from app.services.cloudinary.cloudinary import init_cloudinary

# Import Scheduler Extensions
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

# Declare scheduler globally so other modules can import or view it
scheduler = BackgroundScheduler(
    executors={'default': ThreadPoolExecutor(5)},
    job_defaults={'coalesce': True, 'max_instances': 1},
    timezone=pytz.timezone("Africa/Lagos")
)


def create_app():
    app = Flask(__name__)

    # Dynamically select which config class to pull depending on environment state
    env = os.getenv('FLASK_ENV', 'development')
    if env == 'production':
        app.config.from_object(ProductionConfig)
    else:
        app.config.from_object(DevelopmentConfig)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    limiter.init_app(app)
    init_cloudinary(app)

    global redis_client
    redis_client = Redis.from_url(
        app.config['REDIS_URL'],
        decode_responses=True
    )

    # Force load models into the application context for migrations
    from app.models.TokenBlocklist import TokenBlocklist
    from app.models.Patient import Patient
    from app.models.PatientDetails import PatientDetails
    from app.models.Hospital import Hospital
    from app.models.Staff import Staff
    from app.models.Role import Role, actor_roles, role_permissions
    from app.models.Permission import Permission
    from app.models.MedicalRecords import LoanRequest
    from app.models.RecordDocuments import RequestDocuments
    from app.models.Loan import Loan
    from app.models.Repayment import Repayment

    # Blueprints
    from app.api.health.routes import health_bp
    from app.api.auth.patient.routes import auth_patient_bp
    from app.api.auth.hospital.routes import auth_hospital_bp
    from app.api.auth.staff.routes import auth_staff_bp
    from app.api.patient.routes import patient_bp
    from app.api.staff.routes import staff_bp
    from app.api.loan.routes import loan_bp

    app.register_blueprint(health_bp, url_prefix='/api/v1/health')
    app.register_blueprint(auth_patient_bp, url_prefix='/api/v1/auth/patient')
    app.register_blueprint(
        auth_hospital_bp, url_prefix='/api/v1/auth/hospital')
    app.register_blueprint(auth_staff_bp, url_prefix='/api/v1/auth/staff')
    app.register_blueprint(patient_bp, url_prefix='/api/v1/patient')
    app.register_blueprint(staff_bp, url_prefix="/api/v1/staff")
    app.register_blueprint(loan_bp, url_prefix="/api/v1/loan")

    # ====================================================================
    # REGISTER CUSTOM MANAGEMENT COMMANDS
    # ====================================================================
    @app.cli.command("seed-permissions")
    def seed_permissions_command():
        """Flask CLI integration hook to safely force populate database rules."""
        logger.info("Booting core system database permissions synchronizer...")

        # We push the runtime context explicitly right here
        with app.app_context():
            # Import inside context to avoid any circular dependency traps
            from app.__init__ import seed_system_permissions_and_roles
            seed_system_permissions_and_roles()

        logger.info("Permissions synchronization complete.")

    # ====================================================================
    # INITIALIZE BACKGROUND SCHEDULER
    # ====================================================================
    # Prevents Werkzeug's reload thread from spinning up a second duplicate scheduler instance
    if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        # Import your job function safely inside factory to prevent circular reference cycles
        from app.services.scheduler.apscheduler import continuous_ping

        # Setup jobs
        scheduler.add_job(
            id='ping_server',
            func=continuous_ping,
            trigger='interval',
            minutes=10,
            replace_existing=True
        )

        # CHECK IF THE SCHEDULER IS ALREADY RUNNING FIRST
        if not scheduler.running:
            scheduler.start()
            atexit.register(lambda: scheduler.shutdown())
            logger.info("Scheduler started with Africa/Lagos time tracking.")
        else:
            logger.warning(
                "Scheduler already active, skipping initialization.")

    # ====================================================================
    # GLOBAL API ERROR HANDLERS (Registered directly on the active 'app')
    # ====================================================================

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

        logger.info("INTEGRITY ERROR:", error)
        logger.info("ORIGINAL:", error.orig)

        return {
            "status": "ERROR",
            "code": 409,
            "message": "A record duplicate conflict occurred."
        }, 409

    return app


@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    # Import the model here to avoid circular imports
    from app.models.TokenBlocklist import TokenBlocklist
    jti = jwt_payload["jti"]

    token = db.session.execute(
        db.select(TokenBlocklist).filter_by(jti=jti)
    ).scalar_one_or_none()

    # If token is found in the blocklist table, returns True (Access Denied)
    # If token is NOT found, returns False (Access Granted)
    return token is not None


# Function to add roles and permissions
def seed_system_permissions_and_roles():
    """Idempotently populates core permissions and maps them to default roles."""
    from app.models.Permission import Permission
    from app.models.Role import Role
    from app import db

    # 1. Define ALL system permissions.
    system_permissions = [  # All permissions
        # General Permissions
        "hospital:manage_personal_data",
        "staff:manage_personal_data",
        "patient:manage_personal_data",
        # Hospital Administration
        "hospital:manage_staff",
        "hospital:manage_roles",
        "hospital:view_analytics",
        # Medical Records & Consultations
        "medical_record:read",
        "medical_record:write",
        # Prescriptions & Labs
        "lab:upload_results",
        "lab:view_results",
        # Patients & Finance
        "patient:submit_kyc",
        "loan:apply",
        "loan:approve",
        "loan:manage_requests",
        "loan:view_repayment",
        "loan:history",
    ]
    hospital_admin_allowed = [  # Hospital Admin permissions
        "hospital:manage_staff",
        "hospital:manage_roles",
        "hospital:view_analytics",
        "loan:manage_requests",
        "hospital:manage_personal_data"
    ]
    doctor_allowed = [  # Doctor permissions
        "medical_record:read",
        "medical_record:write",
        "lab:upload_results",
        "loan:apply",
        "loan:manage_requests",
        "staff:manage_personal_data"
    ]
    patient_allowed = [  # Patient permissions
        "patient:manage_personal_data",
        "patient:submit_kyc",
        "loan:view_repayment",
        "loan:history",
    ]

    try:
        # 2. Seed missing permissions safely
        permission_objects = {}
        for perm_name in system_permissions:
            perm = db.session.execute(db.select(Permission).filter_by(
                name=perm_name)).scalar_one_or_none()
            if not perm:
                perm = Permission(name=perm_name)
                db.session.add(perm)
                logger.info(f"Created system permission: '{perm_name}'")
            permission_objects[perm_name] = perm

        # Flush variations to DB so objects obtain relational state
        db.session.flush()

        # 3. Helper function to ensure roles exist
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

        # 4. Map Permissions to Roles (Idempotently)
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

        # Super Admins receive all system permissions
        for target_perm in permission_objects.values():
            if target_perm not in super_admin_role.permissions:
                super_admin_role.permissions.append(target_perm)

        db.session.commit()
        logger.info(
            "Permissions and Role configurations successfully synchronized.")

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error occurred while seeding permissions: {str(e)}")
        print("Warning: Auto-seeding permissions failed! Check logs for details.")
