import json

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from content.auth import require_auth
from content.models import Organization, ScrapingSource, User

ADMIN_PROFILE = User.ProfileType.ADMIN

ALLOWED_FIELDS = {
    "name", "url", "target_profile",
    "country", "domain_names", "interval_minutes", "llm_fallback_enabled",
    "enabled", "quality", "crawl_depth", "crawl_max_pages",
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
@require_auth(roles=[ADMIN_PROFILE])
@require_http_methods(["GET", "POST"])
def admin_sources_collection(request):
    if request.method == "GET":
        sources = ScrapingSource.objects.select_related("organization").all().order_by("key")
        return JsonResponse({"count": sources.count(), "results": [_serialize(s) for s in sources[:500]]})

    # POST — create
    body = _parse_body(request)
    if body is None:
        return JsonResponse({"detail": "Invalid JSON body."}, status=400)

    key = str(body.get("key") or "").strip()
    name = str(body.get("name") or "").strip()
    url = str(body.get("url") or "").strip()
    org_id_str = str(body.get("organization_id") or "").strip()

    if not all([key, name, url, org_id_str]):
        return JsonResponse({"detail": "key, name, url, and organization_id are required."}, status=400)

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
        organization_token=org_id_str,
        target_profile=str(body.get("target_profile") or "student"),
        country=str(body.get("country") or "").strip().upper(),
        domain_names=body.get("domain_names") or [],
        interval_minutes=int(body.get("interval_minutes") or 360),
        llm_fallback_enabled=bool(body.get("llm_fallback_enabled", True)),
        enabled=bool(body.get("enabled", True)),
        quality=str(body.get("quality") or "real"),
        crawl_depth=int(body.get("crawl_depth") or 1),
        crawl_max_pages=int(body.get("crawl_max_pages") or 25),
        crawl_match_patterns=body.get("crawl_match_patterns") or [],
        crawl_exclude_patterns=body.get("crawl_exclude_patterns") or [],
        auto_publish_enabled=bool(body.get("auto_publish_enabled", False)),
    )
    source.refresh_from_db()
    return JsonResponse(_serialize(source), status=201)


@csrf_exempt
@require_auth(roles=[ADMIN_PROFILE])
@require_http_methods(["GET", "PATCH", "DELETE"])
def admin_source_detail(request, key: str):
    try:
        source = ScrapingSource.objects.select_related("organization").get(key=key)
    except ScrapingSource.DoesNotExist:
        return JsonResponse({"detail": "Source not found."}, status=404)

    if request.method == "GET":
        return JsonResponse(_serialize(source))

    if request.method == "DELETE":
        source.delete()
        return HttpResponse(status=204)

    # PATCH — partial update
    body = _parse_body(request)
    if body is None:
        return JsonResponse({"detail": "Invalid JSON body."}, status=400)

    # Handle organization FK separately — not in the generic loop
    if "organization_id" in body:
        oid = body["organization_id"]
        if oid is None:
            source.organization = None
        else:
            try:
                source.organization = Organization.objects.get(id=oid)
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
