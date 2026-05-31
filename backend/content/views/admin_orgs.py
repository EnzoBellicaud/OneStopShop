import json

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse

from content.auth import require_auth
from content.models import Organization, User

ADMIN_PROFILE = User.ProfileType.ADMIN

VALID_TYPES = {t for t, _ in Organization.OrganizationType.choices}


def _json_error(error: str, message: str, status: int) -> JsonResponse:
    return JsonResponse({"error": error, "message": message}, status=status)


def _serialize_org(org: Organization) -> dict:
    return {
        "id": str(org.id),
        "name": org.name,
        "type": org.type,
        "country": org.country,
        "website": org.website,
    }


@csrf_exempt
@require_auth(roles=[ADMIN_PROFILE])
@require_http_methods(["POST"])
def admin_organization_collection(request):
    try:
        body = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return _json_error("validation_error", "Invalid JSON body.", 400)

    name = str(body.get("name") or "").strip()
    org_type = str(body.get("type") or "").strip()
    country = str(body.get("country") or "").strip().upper()
    website = str(body.get("website") or "").strip()

    if not name:
        return _json_error("validation_error", "name is required.", 400)
    if org_type not in VALID_TYPES:
        return _json_error("validation_error", f"type must be one of: {', '.join(sorted(VALID_TYPES))}.", 400)
    if not country or len(country) != 2:
        return _json_error("validation_error", "country must be a 2-letter ISO code.", 400)

    org = Organization.objects.create(
        name=name,
        type=org_type,
        country=country,
        website=website,
    )
    return JsonResponse(_serialize_org(org), status=201)
