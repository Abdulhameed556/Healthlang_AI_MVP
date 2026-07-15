"""
Admin Panel email templates.

Each template function returns a ``dict`` with ``subject``, ``text`` and
``html`` keys, ready to hand to :class:`EmailClient.send`.

Templates:
- otp_login_email     : OTP code for admin login verification
- invite_admin_user_email : invite link for a new admin panel user
"""
from __future__ import annotations

from admin.src.core.config import settings
from admin.src.infrastructure.redis.otp_store import OTP_TTL_SECONDS

_OTP_EXPIRY_MINUTES = OTP_TTL_SECONDS // 60


def otp_login_email(otp: str) -> dict[str, str]:
    """Email body for the login OTP step."""
    subject = "Your Admin Panel login code"
    text = (
        f"Your Admin Panel login code is: {otp}\n\n"
        f"This code expires in {_OTP_EXPIRY_MINUTES} minutes. "
        "If you did not try to sign in, you can ignore this email."
    )
    html = (
        "<div style=\"font-family:Arial,sans-serif;font-size:15px;color:#1a1a1a\">"
        "<p>Your Admin Panel login code is:</p>"
        f"<p style=\"font-size:28px;font-weight:bold;letter-spacing:4px\">{otp}</p>"
        f"<p>This code expires in {_OTP_EXPIRY_MINUTES} minutes. "
        "If you did not try to sign in, you can ignore this email.</p>"
        "</div>"
    )
    return {"subject": subject, "text": text, "html": html}


def invite_admin_user_email(invite_link: str, role: str) -> dict[str, str]:
    """Email body inviting a new Admin Panel user to set their password."""
    subject = f"You've been invited to {settings.app_name} Admin Panel"
    text = (
        f"You've been invited to join the {settings.app_name} Admin Panel "
        f"as {role}.\n\n"
        f"Set your password to activate your account: {invite_link}\n\n"
        "If you weren't expecting this invitation, you can ignore this email."
    )
    html = (
        "<div style=\"font-family:Arial,sans-serif;font-size:15px;color:#1a1a1a\">"
        f"<p>You've been invited to join the {settings.app_name} Admin Panel "
        f"as <strong>{role}</strong>.</p>"
        f"<p><a href=\"{invite_link}\">Set your password to activate your account</a></p>"
        "<p>If you weren't expecting this invitation, you can ignore this email.</p>"
        "</div>"
    )
    return {"subject": subject, "text": text, "html": html}
