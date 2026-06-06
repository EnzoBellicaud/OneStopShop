import json

from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from content.auth import require_auth
from content.models import MockOpportunity, User

ADMIN_PROFILE = User.ProfileType.ADMIN


def _serialize(item: MockOpportunity) -> dict:
    return {
        "id": str(item.id),
        "title": item.title,
        "description": item.description,
        "offer_type": item.offer_type,
        "target_profile": item.target_profile,
        "created_at": item.created_at.isoformat(),
    }


@csrf_exempt
@require_auth(roles=[ADMIN_PROFILE])
@require_http_methods(["GET", "POST"])
def list_create(request):
    if request.method == "GET":
        items = [_serialize(i) for i in MockOpportunity.objects.all()]
        return JsonResponse({"count": len(items), "results": items})

    body = json.loads(request.body)
    title = str(body.get("title", "")).strip()
    description = str(body.get("description", "")).strip()
    if not title:
        return JsonResponse({"detail": "title is required"}, status=400)

    item = MockOpportunity.objects.create(
        title=title,
        description=description,
        offer_type=str(body.get("offer_type", "internship")),
        target_profile=str(body.get("target_profile", "student")),
    )
    return JsonResponse(_serialize(item), status=201)


@csrf_exempt
@require_auth(roles=[ADMIN_PROFILE])
@require_http_methods(["DELETE"])
def item_detail(request, pk):
    item = get_object_or_404(MockOpportunity, pk=pk)
    item.delete()
    return HttpResponse(status=204)
