import json
import threading
from collections import defaultdict
from datetime import timedelta
from uuid import UUID

from django.db.models import Count, Max
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods

from content.auth import require_auth
from content.models import CrawlUrl, ScrapingRun, User
from content.views._utils import _WINDOW_DELTAS, _parse_positive_int

ADMIN_PROFILE = User.ProfileType.ADMIN


def _run_summary(run: ScrapingRun) -> dict:
    return {
        "id": str(run.id),
        "source_key": run.source_key,
        "status": run.status,
        "offers_processed": run.offers_processed,
        "offers_created": run.offers_created,
        "offers_updated": run.offers_updated,
        "offers_unchanged": run.offers_unchanged,
        "offers_skipped": run.offers_skipped,
        "urls_neglected": run.urls_neglected or 0,
        "errors_count": run.errors_count,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "created_at": run.created_at.isoformat(),
    }


@require_auth(roles=['Admin'])
@require_GET
def scraping_runs(request):
    limit = _parse_positive_int(request.GET.get("limit"), default=20, max_value=100)
    runs = list(ScrapingRun.objects.order_by("-created_at")[:limit])
    return JsonResponse({"count": len(runs), "results": [_run_summary(r) for r in runs]})


@require_auth(roles=['Admin'])
@require_GET
def scraping_run_detail(request, run_id: str):
    try:
        parsed_id = UUID(run_id)
    except ValueError:
        return JsonResponse({"detail": "Invalid run id."}, status=400)

    run = ScrapingRun.objects.filter(id=parsed_id).first()
    if run is None:
        return JsonResponse({"detail": "Scraping run not found."}, status=404)

    data = _run_summary(run)
    data["log"] = run.log or []
    data["updated_at"] = run.updated_at.isoformat()
    return JsonResponse(data)


@require_auth(roles=['Admin'])
@require_GET
def scraping_overview(request):
    window_str = request.GET.get("window", "24h")
    if window_str not in _WINDOW_DELTAS:
        return JsonResponse({"detail": f"Invalid window. Use: {', '.join(_WINDOW_DELTAS)}"}, status=400)

    now = timezone.now()
    since = now - _WINDOW_DELTAS[window_str]
    runs = list(ScrapingRun.objects.filter(created_at__gte=since).order_by("created_at"))

    # Pre-fill every expected bucket with zeros so the chart always has full data.
    if window_str == "24h":
        n_buckets, bucket_hours = 24, 1
    elif window_str == "7d":
        n_buckets, bucket_hours = 7, 24
    else:
        n_buckets, bucket_hours = 30, 24

    bucket_map: dict = {}
    for i in range(n_buckets):
        dt = now - timedelta(hours=bucket_hours * (n_buckets - 1 - i))
        if bucket_hours == 1:
            key = dt.strftime("%Y-%m-%dT%H:00:00Z")
        else:
            key = dt.strftime("%Y-%m-%d")
        bucket_map[key] = {"bucket": key, "runs": 0, "errors": 0}

    for run in runs:
        ts = run.created_at
        key = ts.strftime("%Y-%m-%dT%H:00:00Z") if bucket_hours == 1 else ts.strftime("%Y-%m-%d")
        if key in bucket_map:
            bucket_map[key]["runs"] += 1
            bucket_map[key]["errors"] += run.errors_count

    return JsonResponse({
        "window": window_str,
        "runs_total": len(runs),
        "runs_success": sum(1 for r in runs if r.status == "success"),
        "offers_processed": sum(r.offers_processed for r in runs),
        "offers_created": sum(r.offers_created for r in runs),
        "offers_updated": sum(r.offers_updated for r in runs),
        "urls_neglected_total": sum(r.urls_neglected or 0 for r in runs),
        "errors_total": sum(r.errors_count for r in runs),
        "runs_timeline": list(bucket_map.values()),
    })


@require_auth(roles=['Admin'])
@require_GET
def scraping_sources_health(request):
    rows = list(
        CrawlUrl.objects.values("source_key", "status").annotate(count=Count("id"))
    )
    last_scraped = dict(
        CrawlUrl.objects.values("source_key").annotate(ts=Max("last_scraped_at")).values_list("source_key", "ts")
    )

    source_stats: dict = {}
    for row in rows:
        key = row["source_key"]
        if key not in source_stats:
            source_stats[key] = {"pending": 0, "processing": 0, "done": 0, "error": 0, "archived": 0}
        source_stats[key][row["status"]] = row["count"]

    results = []
    for key in sorted(source_stats):
        s = source_stats[key]
        total = sum(s.values())
        ts = last_scraped.get(key)
        results.append({
            "source_key": key,
            "total_urls": total,
            "pending": s.get("pending", 0),
            "processing": s.get("processing", 0),
            "done": s.get("done", 0),
            "error": s.get("error", 0),
            "archived": s.get("archived", 0),
            "last_scraped_at": ts.isoformat() if ts else None,
        })

    return JsonResponse({"results": results})


@require_auth(roles=['Admin'])
@require_GET
def scraping_llm_stats(request):
    window_str = request.GET.get("window", "24h")
    if window_str not in _WINDOW_DELTAS:
        return JsonResponse({"detail": f"Invalid window. Use: {', '.join(_WINDOW_DELTAS)}"}, status=400)

    since = timezone.now() - _WINDOW_DELTAS[window_str]
    runs = list(ScrapingRun.objects.filter(created_at__gte=since).only("log"))

    method_split: dict = defaultdict(int)
    confidence_llm: list = []
    confidence_det: list = []

    for run in runs:
        for entry in (run.log or []):
            if not isinstance(entry, dict):
                continue
            if entry.get("event") != "url_processed":
                continue
            method = entry.get("method")
            if method:
                method_split[method] += 1
            conf = entry.get("confidence")
            if conf is not None:
                if method in ("llm_primary", "llm_fallback"):
                    confidence_llm.append(float(conf))
                elif method == "deterministic":
                    confidence_det.append(float(conf))

    return JsonResponse({
        "window": window_str,
        "method_split": dict(method_split),
        "avg_confidence_llm": round(sum(confidence_llm) / len(confidence_llm), 3) if confidence_llm else None,
        "avg_confidence_deterministic": round(sum(confidence_det) / len(confidence_det), 3) if confidence_det else None,
    })


@csrf_exempt
@require_auth(roles=[ADMIN_PROFILE])
@require_http_methods(["POST"])
def admin_trigger_crawl(request):
    try:
        body = json.loads(request.body) if request.body else {}
    except (json.JSONDecodeError, ValueError):
        body = {}

    source_keys = body.get("source_keys") or None

    def _run():
        from content.scrapers.queue_service import run_crawler
        try:
            run_crawler(source_keys=source_keys)
        except Exception:
            import logging
            logging.getLogger(__name__).exception("Background crawl failed")

    threading.Thread(target=_run, daemon=True).start()

    return JsonResponse(
        {"status": "triggered", "message": "Crawler started in background."},
        status=202,
    )
