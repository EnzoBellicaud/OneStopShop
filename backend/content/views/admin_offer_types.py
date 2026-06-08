import json

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from content.auth import require_auth
from content.models import Offer, OfferType, User
from content.scrapers.offer_type_catalog import invalidate_catalog

ADMIN_PROFILE = User.ProfileType.ADMIN


def _parse_body(request) -> dict | None:
    try:
        return json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return None


def _serialize(ot: OfferType) -> dict:
    return {
        "id": str(ot.id),
        "name": ot.name,
        "description": ot.description,
        "keywords": ot.keywords,
    }


@csrf_exempt
@require_auth(roles=[ADMIN_PROFILE])
@require_http_methods(["GET", "POST"])
def admin_offer_types_collection(request):
    if request.method == "GET":
        offer_types = OfferType.objects.all().order_by("name")
        return JsonResponse({"count": offer_types.count(), "results": [_serialize(ot) for ot in offer_types]})

    # POST — create
    body = _parse_body(request)
    if body is None:
        return JsonResponse({"detail": "Invalid JSON body."}, status=400)

    name = str(body.get("name") or "").strip()
    if not name:
        return JsonResponse({"detail": "name is required."}, status=400)

    if OfferType.objects.filter(name__iexact=name).exists():
        return JsonResponse({"detail": f"Offer type with name '{name}' already exists."}, status=409)

    description = str(body.get("description") or "").strip()
    keywords = str(body.get("keywords") or "").strip()

    offer_type = OfferType.objects.create(name=name, description=description, keywords=keywords)
    invalidate_catalog()
    return JsonResponse(_serialize(offer_type), status=201)


@csrf_exempt
@require_auth(roles=[ADMIN_PROFILE])
@require_http_methods(["GET", "PATCH", "DELETE"])
def admin_offer_type_detail(request, offer_type_id: str):
    try:
        offer_type = OfferType.objects.get(id=offer_type_id)
    except (OfferType.DoesNotExist, Exception):
        return JsonResponse({"detail": "Offer type not found."}, status=404)

    if request.method == "GET":
        return JsonResponse(_serialize(offer_type))

    if request.method == "DELETE":
        if Offer.objects.filter(offer_type_id=offer_type_id).exists():
            return JsonResponse(
                {"detail": "Cannot delete: offer type is in use by existing offers."},
                status=409,
            )
        offer_type.delete()
        invalidate_catalog()
        return HttpResponse(status=204)

    # PATCH — partial update
    body = _parse_body(request)
    if body is None:
        return JsonResponse({"detail": "Invalid JSON body."}, status=400)

    if "name" in body:
        new_name = str(body["name"] or "").strip()
        if not new_name:
            return JsonResponse({"detail": "name cannot be empty."}, status=400)
        if OfferType.objects.filter(name__iexact=new_name).exclude(id=offer_type.id).exists():
            return JsonResponse({"detail": f"Offer type with name '{new_name}' already exists."}, status=409)
        offer_type.name = new_name

    if "description" in body:
        offer_type.description = str(body["description"] or "").strip()

    if "keywords" in body:
        offer_type.keywords = str(body["keywords"] or "").strip()

    offer_type.save()
    invalidate_catalog()
    return JsonResponse(_serialize(offer_type))
