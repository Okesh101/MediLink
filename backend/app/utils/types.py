# app/utils/types.py

from enum import Enum


class Sex(Enum):
    MALE = "Male"
    FEMALE = "Female"


class GrantStatus(Enum):
    GRANTED = "Granted"
    REVOKED = "Revoked"
    EXPIRED = "Expired"


class RequestStatus(Enum):
    PENDING = "Pending"
    APPROVED = "Approved"
    DENIED = "Denied"


class AccessScope(Enum):
    VIEW_AND_CREATE_RECORDS = "view_and_create_records"
