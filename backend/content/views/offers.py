import json as _json
import re
from datetime import date as _date
from math import ceil
from uuid import UUID

from django.db import transaction
from django.db.models import Q, Prefetch
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from content.auth import require_auth, verify_token
from content.matching_service import run_matching_for_offers
from content.models import Domain, Offer, OfferType, Organization, SourceType, TargetProfile, User, UserOrganization, OfferContact
from content.views._utils import _parse_positive_int

OFFER_MANAGER_PROFILES = [User.ProfileType.TEACHER, User.ProfileType.COMPANY]
ADMIN_PROFILE = User.ProfileType.ADMIN


def _contact_to_dict(contact) -> dict | None:
    """Convert a Contact object to a dictionary representation. Return the the dict with null fields if contact is None."""
    if contact is None:
        return None
    
    return {
        "name": contact.contact_name,
        "email": contact.email,
        "phone": contact.phone,
        "linkedin": getattr(contact, "linkedin", None),
    }


def _primary_contact_for_offer(offer) -> dict | None:
    """Get the primary contact for an offer, or the first contact if no primary exists."""
    links = list(getattr(offer, "prefetched_offer_contacts", []))
    primary = next((link for link in links if link.role_label == "primary_contact"), None)
    selected = primary or (links[0] if links else None)
    contact = selected.contact if selected else None
    return _contact_to_dict(contact)


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
        "contact": _primary_contact_for_offer(offer),
    }


def _try_verify_token(request) -> dict | None:
    """Soft token verify — returns payload or None without raising."""
    auth_header = request.META.get("HTTP_AUTHORIZATION", "")
    if not auth_header.startswith("Bearer "):
        return None
    payload = verify_token(auth_header[7:])
    if not payload or payload.get("type") != "access":
        return None
    return payload


def _get_user_org(user: User) -> Organization | None:
    link = UserOrganization.objects.filter(user=user).select_related("organization").first()
    return link.organization if link else None


def _parse_deadline(raw) -> tuple[_date | None, str | None]:
    if not raw:
        return None, None
    try:
        return _date.fromisoformat(str(raw)), None
    except ValueError:
        return None, "deadline must be a valid date (YYYY-MM-DD)."


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
            .prefetch_related(
                "domains",
                Prefetch(
                    "offercontact_set",
                    queryset=OfferContact.objects.select_related("contact"),
                    to_attr="prefetched_offer_contacts",
                ),
            )
        )

        # Org-scoping for authenticated Teacher/Company
        token_payload = _try_verify_token(request)
        if token_payload and token_payload.get("profile") in OFFER_MANAGER_PROFILES:
            authed_user = User.objects.filter(id=token_payload["user_id"]).first()
            if authed_user:
                org = _get_user_org(authed_user)
                queryset = queryset.filter(organization=org) if org else queryset.none()

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
        return JsonResponse(
            {
                "count": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "limit": page_size,
                "results": [_offer_to_dict(row) for row in rows],
            }
        )

    if request.method == "POST":
        return _create_offer(request)

    return JsonResponse({"detail": "Method not allowed."}, status=405)


@csrf_exempt
@require_auth(roles=[ADMIN_PROFILE, User.ProfileType.TEACHER, User.ProfileType.COMPANY])
@require_http_methods(["POST"])
def _create_offer(request):
    try:
        body = _json.loads(request.body)
    except (_json.JSONDecodeError, ValueError):
        return JsonResponse({"detail": "Invalid JSON."}, status=400)

    user = request.auth_user

    title = str(body.get("title") or "").strip()
    summary = str(body.get("summary") or "").strip()
    link = str(body.get("link") or "").strip()
    country = str(body.get("country") or "").strip().upper()
    offer_type_name = str(body.get("offer_type") or "").strip()
    target_profile_name = str(body.get("target_profile") or "").strip()

    if not all([title, summary, link, country, offer_type_name, target_profile_name]):
        return JsonResponse(
            {"detail": "Missing required fields: title, summary, link, country, offer_type, target_profile."},
            status=400,
        )
    if not re.match(r"^[A-Z]{2}$", country):
        return JsonResponse({"detail": "country must be a 2-letter ISO code (e.g. SE)."}, status=400)

    # Resolve organization
    if user.profile in OFFER_MANAGER_PROFILES:
        org = _get_user_org(user)
        if not org:
            return JsonResponse({"error": "no_org", "detail": "No organization linked to your account."}, status=403)
    else:
        # Admin must provide organization_id
        organization_id = str(body.get("organization_id") or "").strip()
        if not organization_id:
            return JsonResponse({"detail": "organization_id is required."}, status=400)
        try:
            parsed_org_id = UUID(organization_id)
        except ValueError:
            return JsonResponse({"detail": "Invalid organization_id."}, status=400)
        org = Organization.objects.filter(id=parsed_org_id).first()
        if not org:
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

    deadline, err = _parse_deadline(body.get("deadline"))
    if err:
        return JsonResponse({"detail": err}, status=400)

    domain_names = body.get("domains", [])

    with transaction.atomic():
        offer = Offer.objects.create(
            title=title,
            summary=summary,
            link=link,
            country=country,
            offer_type=offer_type,
            organization=org,
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
        .prefetch_related(
            "domains",
            Prefetch(
                "offercontact_set",
                queryset=OfferContact.objects.select_related("contact"),
                to_attr="prefetched_offer_contacts",
            ),
        )
        .get(id=offer.id)
    )
    if offer.status == Offer.OfferStatus.PUBLISHED:
        run_matching_for_offers([offer.id])
    return JsonResponse(_offer_to_dict(offer), status=201)


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
            .prefetch_related(
                "domains",
                Prefetch(
                    "offercontact_set",
                    queryset=OfferContact.objects.select_related("contact"),
                    to_attr="prefetched_offer_contacts",
                ),
            )
            .filter(id=parsed_id)
            .first()
        )
        if offer is None:
            return JsonResponse({"detail": "Offer not found."}, status=404)
        return JsonResponse(_offer_to_dict(offer))

    if request.method == "PATCH":
        return _update_offer(request, parsed_id)

    if request.method == "DELETE":
        return _delete_offer(request, parsed_id)

    return JsonResponse({"detail": "Method not allowed."}, status=405)


@require_auth(roles=[ADMIN_PROFILE, User.ProfileType.TEACHER, User.ProfileType.COMPANY])
def _update_offer(request, parsed_id: UUID):
    user = request.auth_user

    offer = (
        Offer.objects.select_related("offer_type", "organization", "source_type", "target_profile")
        .prefetch_related(
            "domains",
            Prefetch(
                "offercontact_set",
                queryset=OfferContact.objects.select_related("contact"),
                to_attr="prefetched_offer_contacts",
            ),
        )
        .filter(id=parsed_id)
        .first()
    )
    if offer is None:
        return JsonResponse({"detail": "Offer not found."}, status=404)

    if user.profile in OFFER_MANAGER_PROFILES:
        org = _get_user_org(user)
        if not org or offer.organization_id != org.id:
            return JsonResponse({"detail": "You can only edit offers from your organization."}, status=403)

    try:
        body = _json.loads(request.body)
    except (_json.JSONDecodeError, ValueError):
        return JsonResponse({"detail": "Invalid JSON."}, status=400)

    update_fields = ["updated_at", "updated_by"]
    offer.updated_by = user

    if "title" in body:
        offer.title = str(body["title"]).strip()
        update_fields.append("title")
    if "summary" in body:
        offer.summary = str(body["summary"]).strip()
        update_fields.append("summary")
    if "link" in body:
        offer.link = str(body["link"]).strip()
        update_fields.append("link")
    if "country" in body:
        country = str(body["country"]).strip().upper()
        if not re.match(r"^[A-Z]{2}$", country):
            return JsonResponse({"detail": "country must be a 2-letter ISO code."}, status=400)
        offer.country = country
        update_fields.append("country")
    if "status" in body:
        new_status = body["status"]
        if new_status not in ("draft", "published", "archived"):
            return JsonResponse({"detail": "status must be draft, published, or archived."}, status=400)
        offer.status = new_status
        update_fields.append("status")
    if "deadline" in body:
        deadline, err = _parse_deadline(body["deadline"])
        if err:
            return JsonResponse({"detail": err}, status=400)
        offer.deadline = deadline
        update_fields.append("deadline")
    if "offer_type" in body:
        ot = OfferType.objects.filter(name__iexact=str(body["offer_type"])).first()
        if not ot:
            return JsonResponse({"detail": f'Offer type "{body["offer_type"]}" not found.'}, status=404)
        offer.offer_type = ot
        update_fields.append("offer_type")
    if "target_profile" in body:
        tp = TargetProfile.objects.filter(name__iexact=str(body["target_profile"])).first()
        if not tp:
            return JsonResponse({"detail": f'Target profile "{body["target_profile"]}" not found.'}, status=404)
        offer.target_profile = tp
        update_fields.append("target_profile")

    offer.save(update_fields=update_fields)

    if "domains" in body:
        domain_names = body["domains"]
        if isinstance(domain_names, list):
            domains_qs = Domain.objects.filter(name__in=domain_names)
            offer.domains.set(domains_qs)

    offer.refresh_from_db()
    if offer.status == Offer.OfferStatus.PUBLISHED:
        run_matching_for_offers([offer.id])
    return JsonResponse(_offer_to_dict(offer))


@require_auth(roles=[ADMIN_PROFILE, User.ProfileType.TEACHER, User.ProfileType.COMPANY])
def _delete_offer(request, parsed_id: UUID):
    user = request.auth_user

    offer = Offer.objects.filter(id=parsed_id).first()
    if offer is None:
        return JsonResponse({"detail": "Offer not found."}, status=404)

    if user.profile in OFFER_MANAGER_PROFILES:
        org = _get_user_org(user)
        if not org or offer.organization_id != org.id:
            return JsonResponse({"detail": "You can only delete offers from your organization."}, status=403)

    offer.delete()
    return HttpResponse(status=204)
