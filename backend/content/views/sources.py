import json
import uuid

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from content.auth import require_auth
from content.models import Organization, ScrapingSource, User, UserOrganization

ADMIN_PROFILE = User.ProfileType.ADMIN
OFFER_MANAGER_PROFILES = [User.ProfileType.TEACHER, User.ProfileType.COMPANY]
VALID_TARGET_PROFILES = {'student', 'company', 'researcher'}

ALLOWED_FIELDS = {
    "name", "url", "target_profile",
    "country", "domain_names", "interval_minutes", "llm_fallback_enabled",
    "enabled", "crawl_depth", "crawl_max_pages",
    "crawl_match_patterns", "crawl_exclude_patterns", "auto_publish_enabled",
}


def _parse_body(request) -> dict | None:
    try:
        return json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return None


def _serialize(s: ScrapingSource) -> dict:
    return {
        "key": s.key,
        "name": s.name,
        "url": s.url,
        "organization_id": str(s.organization_id) if s.organization_id else None,
        "organization_name": s.organization.name if s.organization_id else None,
        "target_profile": s.target_profile,
        "country": s.country,
        "domain_names": s.domain_names,
        "interval_minutes": s.interval_minutes,
        "llm_fallback_enabled": s.llm_fallback_enabled,
        "enabled": s.enabled,
        "quality": s.quality,
        "crawl_depth": s.crawl_depth,
        "crawl_max_pages": s.crawl_max_pages,
        "crawl_match_patterns": s.crawl_match_patterns,
        "crawl_exclude_patterns": s.crawl_exclude_patterns,
        "auto_publish_enabled": s.auto_publish_enabled,
        "auto_publish_mode": "llm" if s.llm_fallback_enabled else "deterministic",
        "created_at": s.created_at.isoformat(),
        "updated_at": s.updated_at.isoformat(),
    }


@csrf_exempt
@require_auth(roles=[ADMIN_PROFILE, *OFFER_MANAGER_PROFILES])
@require_http_methods(["GET", "POST"])
def admin_sources_collection(request):
    if request.method == "GET":
        sources = ScrapingSource.objects.select_related("organization").all().order_by("key")
        if request.auth_user.profile in OFFER_MANAGER_PROFILES:
            org_ids = UserOrganization.objects.filter(
                user=request.auth_user
            ).values_list('organization_id', flat=True)
            sources = sources.filter(organization_id__in=org_ids)
        return JsonResponse({"count": sources.count(), "results": [_serialize(s) for s in sources[:500]]})

    # POST — create
    body = _parse_body(request)
    if body is None:
        return JsonResponse({"detail": "Invalid JSON body."}, status=400)

    key = str(body.get("key") or "").strip() or str(uuid.uuid4())
    name = str(body.get("name") or "").strip()
    url = str(body.get("url") or "").strip()
    tp = str(body.get("target_profile") or "student")
    if tp not in VALID_TARGET_PROFILES:
        return JsonResponse({"detail": f"target_profile must be one of: {', '.join(sorted(VALID_TARGET_PROFILES))}."}, status=400)

    if request.auth_user.profile in OFFER_MANAGER_PROFILES:
        if not all([name, url]):
            return JsonResponse({"detail": "name and url are required."}, status=400)
        link = UserOrganization.objects.filter(
            user=request.auth_user
        ).select_related('organization').first()
        if not link:
            return JsonResponse({"detail": "No organization linked to account."}, status=403)
        org = link.organization
    else:
        org_id_str = str(body.get("organization_id") or "").strip()
        if not all([name, url, org_id_str]):
            return JsonResponse({"detail": "name, url, and organization_id are required."}, status=400)
        try:
            org = Organization.objects.get(id=org_id_str)
        except (Organization.DoesNotExist, ValueError):
            return JsonResponse({"detail": "Organization not found."}, status=404)

    if ScrapingSource.objects.filter(key=key).exists():
        return JsonResponse({"detail": f"Source with key '{key}' already exists."}, status=409)

    source = ScrapingSource.objects.create(
        key=key,
        name=name,
        url=url,
        organization=org,
        organization_token=str(org.id),
        target_profile=tp,
        country=str(body.get("country") or "").strip().upper(),
        domain_names=body.get("domain_names") or [],
        interval_minutes=int(body.get("interval_minutes") or 360),
        llm_fallback_enabled=bool(body.get("llm_fallback_enabled", True)),
        enabled=bool(body.get("enabled", True)),
        quality="real",
        crawl_depth=int(body.get("crawl_depth") or 1),
        crawl_max_pages=int(body.get("crawl_max_pages") or 25),
        crawl_match_patterns=body.get("crawl_match_patterns") or [],
        crawl_exclude_patterns=body.get("crawl_exclude_patterns") or [],
        auto_publish_enabled=bool(body.get("auto_publish_enabled", False)),
    )
    source.refresh_from_db()
    return JsonResponse(_serialize(source), status=201)


@csrf_exempt
@require_auth(roles=[ADMIN_PROFILE, *OFFER_MANAGER_PROFILES])
@require_http_methods(["GET", "PATCH", "DELETE"])
def admin_source_detail(request, key: str):
    try:
        source = ScrapingSource.objects.select_related("organization").get(key=key)
    except ScrapingSource.DoesNotExist:
        return JsonResponse({"detail": "Source not found."}, status=404)

    if request.auth_user.profile in OFFER_MANAGER_PROFILES:
        user_org_ids = list(UserOrganization.objects.filter(
            user=request.auth_user
        ).values_list('organization_id', flat=True))
        if source.organization_id not in user_org_ids:
            return JsonResponse({"detail": "Not found."}, status=404)

    if request.method == "GET":
        return JsonResponse(_serialize(source))

    if request.method == "DELETE":
        source.delete()
        return HttpResponse(status=204)

    # PATCH — partial update
    body = _parse_body(request)
    if body is None:
        return JsonResponse({"detail": "Invalid JSON body."}, status=400)

    # Offer managers cannot re-assign organization
    if request.auth_user.profile in OFFER_MANAGER_PROFILES:
        body.pop('organization_id', None)

    if "target_profile" in body:
        tp = str(body["target_profile"])
        if tp not in VALID_TARGET_PROFILES:
            return JsonResponse({"detail": f"target_profile must be one of: {', '.join(sorted(VALID_TARGET_PROFILES))}."}, status=400)

    # Handle organization FK separately — not in the generic loop
    if "organization_id" in body:
        oid = body["organization_id"]
        if oid is None:
            source.organization = None
            source.organization_token = ""
        else:
            try:
                org = Organization.objects.get(id=oid)
                source.organization = org
                source.organization_token = str(org.id)
            except (Organization.DoesNotExist, ValueError):
                return JsonResponse({"detail": "Organization not found."}, status=404)

    bool_fields = {"llm_fallback_enabled", "enabled", "auto_publish_enabled"}
    int_fields = {"interval_minutes", "crawl_depth", "crawl_max_pages"}
    list_fields = {"domain_names", "crawl_match_patterns", "crawl_exclude_patterns"}

    for field in ALLOWED_FIELDS:
        if field not in body:
            continue
        val = body[field]
        if field in bool_fields:
            setattr(source, field, bool(val))
        elif field in int_fields:
            setattr(source, field, int(val))
        elif field in list_fields:
            setattr(source, field, list(val) if isinstance(val, list) else [])
        else:
            setattr(source, field, str(val).strip())

    source.save()
    source.refresh_from_db()
    return JsonResponse(_serialize(source))
