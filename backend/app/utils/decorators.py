# app/utils/decorators.py

from app import db
from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity, get_jwt
from app.models.Staff import Staff
from app.models.Hospital import Hospital
from app.models.Patient import Patient


def _get_current_actor():
    """Helper function to load the authenticated actor (Staff, Hospital, or Patient)

    based on JWT identity and actor_type claim.
    """

    actor_id = get_jwt_identity()
    claims = get_jwt()
    # Expecting: 'staff', 'hospital_admin', or 'patient'
    actor_type = claims.get("actor_type")

    print("=== AUTH DEBUG ===")
    print("JWT IDENTITY:", actor_id)
    print("JWT CLAIMS:", claims)
    print("ACTOR TYPE:", actor_type)

    if actor_type == "hospital_admin":
        return db.session.get(Hospital, actor_id)
    elif actor_type == "patient":
        return db.session.get(Patient, actor_id)
    elif actor_type == "staff":
        return db.session.get(Staff, actor_id)
    else:
        actor = None

    print("ACTOR:", actor)

    if actor:
        print("ACTOR TYPE:", type(actor).__name__)
        print("ROLES:", [r.name for r in getattr(actor, "roles", [])])

    return actor


def roles_required(*role_names: str):
    """Protects endpoints by verifying if the current actor holds at least one required role.

    Must be placed BELOW @jwt_required().
    Usage: @roles_required("Doctor", "Patient", "Hospital Admin")
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            actor = _get_current_actor()

            if not actor:
                return (
                    jsonify(
                        {
                            "status": "ERROR",
                            "code": 401,
                            "message": "Authenticated user/actor not found.",
                        }
                    ),
                    401,
                )

            # Extract actor's role names dynamically
            actor_roles = {role.name for role in getattr(actor, "roles", [])}

            # Super Admin override
            if "Super Admin" in actor_roles:
                return fn(*args, **kwargs)

            # Verify if actor has at least one of the requested roles
            if not any(r in actor_roles for r in role_names):
                return (
                    jsonify(
                        {
                            "status": "ERROR",
                            "code": 403,
                            "message": (
                                "Forbidden! You do not have the required role"
                                " to access this resource."
                            ),
                        }
                    ),
                    403,
                )

            return fn(*args, **kwargs)

        return wrapper

    return decorator


def permissions_required(*required_permissions: str, match_all: bool = False):
    """Protects endpoints by verifying fine-grained permissions.

    Must be placed BELOW @jwt_required().
    Usage: @permissions_required("medical_record:read", "medical_record:write", match_all=True)
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            actor = _get_current_actor()

            if not actor:
                return (
                    jsonify(
                        {
                            "status": "ERROR",
                            "code": 401,
                            "message": "Authenticated user/actor not found.",
                        }
                    ),
                    401,
                )

            actor_roles = getattr(actor, "roles", [])
            role_names = {r.name for r in actor_roles}

            # Global Super Admin override
            if "Super Admin" in role_names:
                return fn(*args, **kwargs)

            # Compile set of all permissions across all assigned roles
            actor_permissions = {
                perm.name
                for role in actor_roles
                for perm in getattr(role, "permissions", [])
            }

            # Evaluation check based on matching strategy
            if match_all:
                has_access = all(
                    perm in actor_permissions for perm in required_permissions
                )
            else:
                has_access = any(
                    perm in actor_permissions for perm in required_permissions
                )

            if not has_access:
                return (
                    jsonify(
                        {
                            "status": "ERROR",
                            "code": 403,
                            "message": (
                                "Unauthorized. Missing required permissions:"
                                f" {list(required_permissions)}"
                            ),
                        }
                    ),
                    403,
                )

            return fn(*args, **kwargs)

        return wrapper

    return decorator
