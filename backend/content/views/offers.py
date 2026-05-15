from math import ceil
from uuid import UUID

from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from content.models import Offer
from content.views._utils import _parse_positive_int


def _offer_to_dict(offer: Offer) -> dict:
    return {
        "id": str(offer.id),
        "title": offer.title,
        "summary": offer.summary,
        "link": offer.link,
        "country": offer.country,
        "status": offer.status,
        "offer_type": offer.offer_type.name,
        "organization": {
            "id": str(offer.organization.id),
            "name": offer.organization.name,
            "type": offer.organization.type,
            "country": offer.organization.country,
        },
        "source_type": offer.source_type.name,
        "target_profile": offer.target_profile.name,
        "domains": [domain.name for domain in offer.domains.all()],
        "details": offer.details,
        "created_at": offer.created_at.isoformat(),
        "updated_at": offer.updated_at.isoformat(),
    }


@require_GET
def offers(request):
    queryset = (
        Offer.objects.select_related(
            "offer_type",
            "organization",
            "source_type",
            "target_profile",
        )
        .prefetch_related("domains")
        .order_by("title")
    )

    status = request.GET.get("status")
    if status:
        queryset = queryset.filter(status=status)

    offer_type = request.GET.get("offer_type")
    if offer_type:
        queryset = queryset.filter(offer_type__name__iexact=offer_type)

    organization = request.GET.get("organization")
    if organization:
        queryset = queryset.filter(organization__name__icontains=organization)

    target_profile = request.GET.get("target_profile")
    if target_profile:
        queryset = queryset.filter(target_profile__name__iexact=target_profile)

    domain = request.GET.get("domain")
    if domain:
        queryset = queryset.filter(domains__name=domain)

    country = request.GET.get("country")
    if country:
        queryset = queryset.filter(country__iexact=country.strip())

    search_term = request.GET.get("q")
    if search_term:
        queryset = queryset.filter(
            Q(title__icontains=search_term)
            | Q(summary__icontains=search_term)
            | Q(organization__name__icontains=search_term)
        )

    queryset = queryset.distinct()

    legacy_limit = request.GET.get("limit")
    page_size_param = request.GET.get("page_size")
    if page_size_param is None and legacy_limit is not None:
        page_size = _parse_positive_int(legacy_limit, default=50, max_value=200)
    else:
        page_size = _parse_positive_int(page_size_param, default=50, max_value=200)

    page = _parse_positive_int(request.GET.get("page"), default=1, max_value=1000000)
    total_count = queryset.count()
    total_pages = ceil(total_count / page_size) if total_count else 0
    offset = (page - 1) * page_size

    rows = list(queryset[offset:offset + page_size])
    payload = [_offer_to_dict(row) for row in rows]

    return JsonResponse(
        {
            "count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "limit": page_size,
            "results": payload,
        }
    )


def offer_detail(request, offer_id: str):
    try:
        parsed_id = UUID(offer_id)
    except ValueError:
        return JsonResponse({"detail": "Invalid offer id."}, status=400)

    if request.method == "GET":
        offer = (
            Offer.objects.select_related(
                "offer_type", "organization", "source_type", "target_profile",
            )
            .prefetch_related("domains")
            .filter(id=parsed_id)
            .first()
        )
        if offer is None:
            return JsonResponse({"detail": "Offer not found."}, status=404)
        return JsonResponse(_offer_to_dict(offer))

    if request.method == "PATCH":
        import json as _json
        from content.jwt_auth import get_user_from_token
        user = get_user_from_token(request)
        if not user:
            return JsonResponse({"detail": "Unauthorized."}, status=401)
        if user.profile != "Admin":
            return JsonResponse({"detail": "Admin access required."}, status=403)
        try:
            body = _json.loads(request.body)
        except (_json.JSONDecodeError, ValueError):
            return JsonResponse({"detail": "Invalid JSON."}, status=400)
        new_status = body.get("status")
        if new_status not in ("draft", "published", "archived"):
            return JsonResponse({"detail": "status must be draft, published, or archived."}, status=400)
        offer = (
            Offer.objects.select_related(
                "offer_type", "organization", "source_type", "target_profile",
            )
            .prefetch_related("domains")
            .filter(id=parsed_id)
            .first()
        )
        if offer is None:
            return JsonResponse({"detail": "Offer not found."}, status=404)
        offer.status = new_status
        offer.save(update_fields=["status", "updated_at"])
        return JsonResponse(_offer_to_dict(offer))

    return JsonResponse({"detail": "Method not allowed."}, status=405)
