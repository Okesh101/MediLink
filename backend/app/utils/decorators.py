# app/utils/decorators.py

from app import db
from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity, get_jwt
from app.models.Staff import Staff
from app.models.Hospital import Hospital
from app.models.Patient import Patient
from app.utils.helpers import as_uuid


def _get_current_actor():
    """Load the authenticated actor (Staff, Hospital, or Patient)
    based on JWT identity and actor_type claim.
    """

    actor_id = as_uuid(get_jwt_identity())
    claims = get_jwt()
    actor_type = claims.get("actor_type")

    if actor_id is None:
        return None

    if actor_type == "hospital_admin":
        return db.session.get(Hospital, actor_id)
    if actor_type == "patient":
        return db.session.get(Patient, actor_id)
    if actor_type == "staff":
        return db.session.get(Staff, actor_id)
    return None


def actor_types_required(*allowed_types: str):
    """Restrict an endpoint to one or more JWT actor types.

    Must be placed BELOW @jwt_required().
    Usage: @actor_types_required("staff", "patient")
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            actor_type = claims.get("actor_type")

            if actor_type not in allowed_types:
                return jsonify({
                    "status": "ERROR",
                    "code": 403,
                    "message": (
                        "Forbidden. This action is not available "
                        "for the current account type."
                    ),
                }), 403

            return fn(*args, **kwargs)

        return wrapper

    return decorator


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

            actor_roles = {role.name for role in getattr(actor, "roles", [])}

            if "Super Admin" in actor_roles:
                return fn(*args, **kwargs)

            if not any(r in actor_roles for r in role_names):
                return (
                    jsonify(
                        {
                            "status": "ERROR",
                            "code": 403,
                            "message": (
                                "Forbidden. You do not have the required role "
                                "to access this resource."
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

            if "Super Admin" in role_names:
                return fn(*args, **kwargs)

            actor_permissions = {
                perm.name
                for role in actor_roles
                for perm in getattr(role, "permissions", [])
            }

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
                                "Forbidden. Missing required permission(s) "
                                f"for this action."
                            ),
                        }
                    ),
                    403,
                )

            return fn(*args, **kwargs)

        return wrapper

    return decorator
