"""Value objects for users."""
from enum import StrEnum


class UserRole(StrEnum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    DOCTOR = "doctor"
    NURSE = "nurse"
    LAB_SCIENTIST = "lab_scientist"
    PHARMACIST = "pharmacist"
    FRONT_DESK = "front_desk"


class UserStatus(StrEnum):
    INVITED = "invited"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    INVITATION_DECLINED = "invitation_declined"


class UserAuthMethod(StrEnum):
    EMAIL_PASSWORD = "email_password"
    GOOGLE_OAUTH = "google_oauth"
