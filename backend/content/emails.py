import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def _smtp_ready() -> bool:
    return bool(getattr(settings, "EMAIL_HOST", ""))


def send_registration_pending_email(user) -> None:
    """Notify Teacher/Company their account is pending admin approval."""
    if not _smtp_ready():
        logger.info("[EMAIL PLACEHOLDER] Registration pending: %s <%s>", user.username, user.email)
        return
    send_mail(
        subject="Your SUNRISE OSS registration is pending approval",
        message=(
            f"Hi {user.first_name or user.username},\n\n"
            "Your registration has been received and is pending admin approval.\n"
            "You will be notified once your account is activated.\n\n"
            "— SUNRISE OSS Team"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,
    )


def send_approval_email(user) -> None:
    """Notify user their account has been approved."""
    if not _smtp_ready():
        logger.info("[EMAIL PLACEHOLDER] Approved: %s <%s>", user.username, user.email)
        return
    send_mail(
        subject="Your SUNRISE OSS account has been approved",
        message=(
            f"Hi {user.first_name or user.username},\n\n"
            "Your account has been approved. You can now log in.\n\n"
            "— SUNRISE OSS Team"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,
    )


def send_rejection_email(user, notes: str = "") -> None:
    """Notify user their account registration was rejected."""
    if not _smtp_ready():
        logger.info("[EMAIL PLACEHOLDER] Rejected: %s <%s>", user.username, user.email)
        return
    reason_line = f"Reason: {notes}\n\n" if notes else "\n"
    send_mail(
        subject="SUNRISE OSS registration update",
        message=(
            f"Hi {user.first_name or user.username},\n\n"
            "We were unable to approve your account registration.\n"
            + reason_line
            + "— SUNRISE OSS Team"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,
    )


def send_email_verification_email(user, verification_token: str) -> None:
    """
    Send email verification link.

    NOT called anywhere yet — token generation/storage is deferred.
    Wire this when SMTP provider is confirmed and a token model is added.
    """
    verification_url = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"
    if not _smtp_ready():
        logger.info(
            "[EMAIL PLACEHOLDER] Verification link for %s <%s>: %s",
            user.username,
            user.email,
            verification_url,
        )
        return
    send_mail(
        subject="Verify your SUNRISE OSS email address",
        message=(
            f"Hi {user.first_name or user.username},\n\n"
            f"Click the link below to verify your email address:\n{verification_url}\n\n"
            "— SUNRISE OSS Team"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,
    )
