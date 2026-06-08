import json

from django.db.models import Count
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from content.auth import require_auth
from content.models import Organization, User

ADMIN_PROFILE = User.ProfileType.ADMIN

VALID_TYPES = {t for t, _ in Organization.OrganizationType.choices}


def _json_error(error: str, message: str, status: int) -> JsonResponse:
    return JsonResponse({"error": error, "message": message}, status=status)


def _serialize_org(org: Organization, offers_count: int = 0, sources_count: int = 0) -> dict:
    return {
        "id": str(org.id),
        "name": org.name,
        "type": org.type,
        "country": org.country,
        "website": org.website,
        "offers_count": offers_count,
        "sources_count": sources_count,
    }


@csrf_exempt
@require_auth(roles=[ADMIN_PROFILE])
@require_http_methods(["GET", "POST"])
def admin_organization_collection(request):
    if request.method == "GET":
        orgs = Organization.objects.annotate(
            offers_count=Count("offers", distinct=True),
            sources_count=Count("scraping_sources", distinct=True),
        ).order_by("name")
        results = [_serialize_org(o, o.offers_count, o.sources_count) for o in orgs]
        return JsonResponse({"count": len(results), "results": results})

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


@csrf_exempt
@require_auth(roles=[ADMIN_PROFILE])
@require_http_methods(["PATCH", "DELETE"])
def admin_organization_detail(request, org_id: str):
    try:
        org = Organization.objects.get(id=org_id)
    except (Organization.DoesNotExist, ValueError):
        return _json_error("not_found", "Organization not found.", 404)

    if request.method == "DELETE":
        if org.offers.exists():
            return _json_error(
                "has_offers",
                "Cannot delete: offers reference this organization. Reassign them first.",
                409,
            )
        if org.scraping_sources.exists():
            return _json_error(
                "has_sources",
                "Cannot delete: scraping sources reference this organization. Unlink them first.",
                409,
            )
        org.delete()
        return JsonResponse({}, status=204)

    # PATCH
    try:
        body = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return _json_error("validation_error", "Invalid JSON body.", 400)

    if "name" in body:
        name = str(body["name"]).strip()
        if not name:
            return _json_error("validation_error", "name cannot be empty.", 400)
        org.name = name
    if "type" in body:
        t = str(body["type"]).strip()
        if t not in VALID_TYPES:
            return _json_error("validation_error", f"type must be one of: {', '.join(sorted(VALID_TYPES))}.", 400)
        org.type = t
    if "country" in body:
        c = str(body["country"]).strip().upper()
        if len(c) != 2:
            return _json_error("validation_error", "country must be a 2-letter ISO code.", 400)
        org.country = c
    if "website" in body:
        org.website = str(body["website"]).strip()
    org.save()

    annotated = Organization.objects.annotate(
        offers_count=Count("offers", distinct=True),
        sources_count=Count("scraping_sources", distinct=True),
    ).get(id=org.id)
    return JsonResponse(_serialize_org(annotated, annotated.offers_count, annotated.sources_count))
