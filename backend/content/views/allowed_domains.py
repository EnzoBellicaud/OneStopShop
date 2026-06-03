import json
from uuid import UUID

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from content.auth import require_auth
from content.models import AllowedDomain, Organization, User

ADMIN_PROFILE = User.ProfileType.ADMIN


def _json_error(error: str, message: str, status: int) -> JsonResponse:
    return JsonResponse({"error": error, "message": message}, status=status)


def _parse_body(request) -> dict | None:
    try:
        return json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return None


def _parse_uuid(value: str) -> UUID | None:
    try:
        return UUID(value)
    except (TypeError, ValueError):
        return None


def _serialize_domain(domain: AllowedDomain) -> dict:
    return {
        "id": str(domain.id),
        "domain": domain.domain,
        "organization": domain.organization.name,
        "organization_id": str(domain.organization.id),
        "description": domain.description,
        "created_at": domain.created_at.isoformat(),
    }


def _validate_domain_string(value: str) -> str | None:
    """Return normalized domain or None if invalid. Also returns error message on failure."""
    normalized = value.lower().strip()
    if not normalized:
        return None, "domain cannot be blank."
    if "@" in normalized:
        return None, "domain must not include '@'."
    if normalized.startswith("http"):
        return None, "domain must not include a URL scheme."
    if "." not in normalized:
        return None, "domain must contain at least one dot."
    return normalized, None


@require_auth(roles=[ADMIN_PROFILE])
@require_http_methods(["GET"])
def allowed_domains_collection_get(request):
    domains = AllowedDomain.objects.select_related("organization").order_by("domain")
    return JsonResponse({"results": [_serialize_domain(d) for d in domains]})


@csrf_exempt
@require_auth(roles=[ADMIN_PROFILE])
@require_http_methods(["GET", "POST"])
def allowed_domains_collection(request):
    if request.method == "GET":
        domains = list(AllowedDomain.objects.select_related("organization").order_by("domain"))
        results = [_serialize_domain(d) for d in domains]
        return JsonResponse({"count": len(results), "results": results})

    body = _parse_body(request)
    if body is None:
        return _json_error("validation_error", "Invalid JSON body.", 400)

    raw_domain = str(body.get("domain") or "")
    normalized, err = _validate_domain_string(raw_domain)
    if err:
        return _json_error("validation_error", err, 400)

    org_id = _parse_uuid(str(body.get("organization_id") or ""))
    if org_id is None:
        return _json_error("validation_error", "Invalid organization_id.", 400)

    org = Organization.objects.filter(id=org_id).first()
    if org is None:
        return _json_error("not_found", "Organization not found.", 404)

    description = str(body.get("description") or "").strip()

    if AllowedDomain.objects.filter(domain=normalized).exists():
        return _json_error("conflict", f"Domain '{normalized}' is already registered.", 409)

    domain_obj = AllowedDomain.objects.create(
        domain=normalized,
        organization=org,
        description=description,
    )
    return JsonResponse(_serialize_domain(domain_obj), status=201)


@csrf_exempt
@require_auth(roles=[ADMIN_PROFILE])
@require_http_methods(["PATCH", "DELETE"])
def allowed_domain_resource(request, domain_id: str):
    parsed_id = _parse_uuid(domain_id)
    if parsed_id is None:
        return _json_error("validation_error", "Invalid domain id.", 400)

    domain_obj = AllowedDomain.objects.select_related("organization").filter(id=parsed_id).first()
    if domain_obj is None:
        return _json_error("not_found", "Allowed domain not found.", 404)

    if request.method == "DELETE":
        domain_obj.delete()
        return JsonResponse({}, status=204)

    body = _parse_body(request)
    if body is None:
        return _json_error("validation_error", "Invalid JSON body.", 400)

    if "domain" in body:
        normalized, err = _validate_domain_string(str(body.get("domain") or ""))
        if err:
            return _json_error("validation_error", err, 400)
        if AllowedDomain.objects.exclude(id=parsed_id).filter(domain=normalized).exists():
            return _json_error("conflict", f"Domain '{normalized}' is already registered.", 409)
        domain_obj.domain = normalized

    if "organization_id" in body:
        org_id = _parse_uuid(str(body.get("organization_id") or ""))
        if org_id is None:
            return _json_error("validation_error", "Invalid organization_id.", 400)
        org = Organization.objects.filter(id=org_id).first()
        if org is None:
            return _json_error("not_found", "Organization not found.", 404)
        domain_obj.organization = org

    if "description" in body:
        domain_obj.description = str(body.get("description") or "").strip()

    domain_obj.save()
    return JsonResponse(_serialize_domain(domain_obj))
