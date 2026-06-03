import json

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse

from content.auth import hash_password, require_auth
from content.models import Organization, User, UserOrganization, UserRole

ADMIN_PROFILE = User.ProfileType.ADMIN


def _json_error(error: str, message: str, status: int) -> JsonResponse:
    return JsonResponse({"error": error, "message": message}, status=status)


def _parse_body(request) -> dict | None:
    try:
        return json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return None


def _serialize_user(user: User) -> dict:
    return {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "profile": user.profile,
        "is_active": user.is_active,
        "approval_status": user.approval_status,
        "email_verified": user.email_verified,
        "approved_by": user.approved_by.username if user.approved_by else None,
        "approval_notes": user.approval_notes,
        "created_at": user.created_at.isoformat(),
        "updated_at": user.updated_at.isoformat(),
    }


@csrf_exempt
@require_auth(roles=[ADMIN_PROFILE])
@require_http_methods(["POST"])
def admin_user_collection(request):
    body = _parse_body(request)
    if body is None:
        return _json_error("validation_error", "Invalid JSON body.", 400)

    username = str(body.get("username") or "").strip()
    email = str(body.get("email") or "").strip()
    password = body.get("password") or ""
    profile = str(body.get("profile") or User.ProfileType.STUDENT).strip()
    first_name = str(body.get("first_name") or "").strip()
    last_name = str(body.get("last_name") or "").strip()
    organization_id = body.get("organization_id")

    if not username or len(username) < 3:
        return _json_error("validation_error", "Username must be at least 3 characters.", 400)
    if not email or "@" not in email:
        return _json_error("validation_error", "Invalid email address.", 400)
    if not password or len(password) < 8:
        return _json_error("validation_error", "Password must be at least 8 characters.", 400)

    valid_profiles = {p for p, _ in User.ProfileType.choices}
    if profile not in valid_profiles:
        return _json_error("validation_error", f"profile must be one of: {', '.join(sorted(valid_profiles))}.", 400)

    if User.objects.filter(username=username).exists():
        return _json_error("conflict", "Username already exists.", 409)
    if User.objects.filter(email=email).exists():
        return _json_error("conflict", "Email already exists.", 409)

    user = User.objects.create(
        username=username,
        email=email,
        password_hash=hash_password(password),
        first_name=first_name,
        last_name=last_name,
        profile=profile,
        is_active=True,
        approval_status=User.ApprovalStatus.APPROVED,
        email_verified=True,
        approved_by=request.auth_user,
    )

    if organization_id:
        from uuid import UUID
        try:
            org_uuid = UUID(str(organization_id))
        except (TypeError, ValueError):
            org_uuid = None

        if org_uuid:
            org = Organization.objects.filter(id=org_uuid).first()
            if org:
                role, _ = UserRole.objects.get_or_create(name="researcher", defaults={"description": "Researcher"})
                UserOrganization.objects.get_or_create(user=user, organization=org, defaults={"role": role})

    return JsonResponse(_serialize_user(user), status=201)
