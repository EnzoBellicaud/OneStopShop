import json as _json
import re
from math import ceil
from uuid import UUID

from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from content.models import Domain, Offer, OfferType, Organization, SourceType, TargetProfile
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
        "deadline": offer.deadline.isoformat() if offer.deadline else None,
        "created_at": offer.created_at.isoformat(),
        "updated_at": offer.updated_at.isoformat(),
    }


@csrf_exempt
def offers(request):
    if request.method == "GET":
        queryset = (
            Offer.objects.select_related(
                "offer_type",
                "organization",
                "source_type",
                "target_profile",
            )
            .prefetch_related("domains")
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

        ordering_param = request.GET.get("ordering", "title")
        if ordering_param not in {"title", "-title", "created_at", "-created_at"}:
            ordering_param = "title"
        queryset = queryset.order_by(ordering_param)

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

    if request.method == "POST":
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

        title = body.get("title", "").strip()
        summary = body.get("summary", "").strip()
        link = body.get("link", "").strip()
        country = body.get("country", "").strip().upper()
        offer_type_name = body.get("offer_type", "").strip()
        organization_id = body.get("organization_id", "").strip()
        target_profile_name = body.get("target_profile", "").strip()

        if not all([title, summary, link, country, offer_type_name, organization_id, target_profile_name]):
            return JsonResponse(
                {"detail": "Missing required fields: title, summary, link, country, offer_type, organization_id, target_profile."},
                status=400,
            )
        if not re.match(r"^[A-Z]{2}$", country):
            return JsonResponse({"detail": "country must be a 2-letter ISO code (e.g. US)."}, status=400)

        try:
            parsed_org_id = UUID(organization_id)
        except ValueError:
            return JsonResponse({"detail": "Invalid organization_id."}, status=400)

        organization = Organization.objects.filter(id=parsed_org_id).first()
        if not organization:
            return JsonResponse({"detail": "Organization not found."}, status=404)
        offer_type = OfferType.objects.filter(name__iexact=offer_type_name).first()
        if not offer_type:
            return JsonResponse({"detail": f'Offer type "{offer_type_name}" not found.'}, status=404)
        target_profile = TargetProfile.objects.filter(name__iexact=target_profile_name).first()
        if not target_profile:
            return JsonResponse({"detail": f'Target profile "{target_profile_name}" not found.'}, status=404)
        source_type = SourceType.objects.filter(name="manual").first()
        if not source_type:
            return JsonResponse({"detail": 'Source type "manual" not found — run seed_lookups.'}, status=500)

        status_val = body.get("status", "draft")
        if status_val not in ("draft", "published", "archived"):
            status_val = "draft"
        domain_names = body.get("domains", [])

        deadline = None
        deadline_raw = body.get("deadline")
        if deadline_raw:
            from datetime import date as _date
            try:
                deadline = _date.fromisoformat(str(deadline_raw))
            except ValueError:
                return JsonResponse({"detail": "deadline must be a valid date (YYYY-MM-DD)."}, status=400)

        with transaction.atomic():
            offer = Offer.objects.create(
                title=title,
                summary=summary,
                link=link,
                country=country,
                offer_type=offer_type,
                organization=organization,
                target_profile=target_profile,
                source_type=source_type,
                status=status_val,
                deadline=deadline,
                created_by=user,
                updated_by=user,
                details={},
            )
            if domain_names:
                domains_qs = Domain.objects.filter(name__in=domain_names)
                offer.domains.set(domains_qs)

        offer = (
            Offer.objects.select_related("offer_type", "organization", "source_type", "target_profile")
            .prefetch_related("domains")
            .get(id=offer.id)
        )
        return JsonResponse(_offer_to_dict(offer), status=201)

    return JsonResponse({"detail": "Method not allowed."}, status=405)


@csrf_exempt
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
        update_fields = ["updated_at"]

        new_status = body.get("status")
        if new_status is not None:
            if new_status not in ("draft", "published", "archived"):
                return JsonResponse({"detail": "status must be draft, published, or archived."}, status=400)
            update_fields.append("status")

        deadline = None
        if "deadline" in body:
            deadline_raw = body["deadline"]
            if deadline_raw:
                from datetime import date as _date
                try:
                    deadline = _date.fromisoformat(str(deadline_raw))
                except ValueError:
                    return JsonResponse({"detail": "deadline must be YYYY-MM-DD."}, status=400)
            update_fields.append("deadline")

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
        if new_status is not None:
            offer.status = new_status
        if "deadline" in body:
            offer.deadline = deadline
        offer.save(update_fields=update_fields)
        return JsonResponse(_offer_to_dict(offer))

    if request.method == "DELETE":
        from content.jwt_auth import get_user_from_token
        user = get_user_from_token(request)
        if not user:
            return JsonResponse({"detail": "Unauthorized."}, status=401)
        if user.profile != "Admin":
            return JsonResponse({"detail": "Admin access required."}, status=403)
        offer = Offer.objects.filter(id=parsed_id).first()
        if offer is None:
            return JsonResponse({"detail": "Offer not found."}, status=404)
        offer.delete()
        return HttpResponse(status=204)

    return JsonResponse({"detail": "Method not allowed."}, status=405)
