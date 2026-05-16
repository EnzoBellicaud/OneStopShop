import json
from math import ceil
from uuid import UUID

from django.db.models import Count, Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from content.auth import require_auth, verify_token
from content.models import ForumAnswer, ForumQuestion, OfferType, User
from content.views._utils import _parse_positive_int


TITLE_MIN_LEN = 5
TITLE_MAX_LEN = 255
BODY_MIN_LEN = 10


def _question_to_dict(q: ForumQuestion, answer_count: int | None = None) -> dict:
    return {
        "id": str(q.id),
        "title": q.title,
        "body": q.body,
        "author": {
            "id": str(q.author.id),
            "username": q.author.username,
        },
        "offer_type": q.offer_type.name if q.offer_type_id else None,
        "offer_type_id": str(q.offer_type_id) if q.offer_type_id else None,
        "answer_count": answer_count if answer_count is not None else q.answers.count(),
        "created_at": q.created_at.isoformat(),
        "updated_at": q.updated_at.isoformat(),
    }


def _answer_to_dict(a: ForumAnswer) -> dict:
    return {
        "id": str(a.id),
        "question_id": str(a.question_id),
        "body": a.body,
        "author": {
            "id": str(a.author.id),
            "username": a.author.username,
        },
        "created_at": a.created_at.isoformat(),
        "updated_at": a.updated_at.isoformat(),
    }


def _maybe_authenticated_user(request) -> User | None:
    auth_header = request.META.get("HTTP_AUTHORIZATION", "")
    if not auth_header.startswith("Bearer "):
        return None
    payload = verify_token(auth_header[7:])
    if not payload or payload.get("type") != "access":
        return None
    user_id = payload.get("user_id")
    if not user_id:
        return None
    return User.objects.filter(id=user_id, is_active=True).first()


def _require_auth_inline(request) -> tuple[User | None, JsonResponse | None]:
    """Returns (user, None) on success or (None, JsonResponse) on failure."""
    auth_header = request.META.get("HTTP_AUTHORIZATION", "")
    if not auth_header.startswith("Bearer "):
        return None, JsonResponse({"detail": "Authentication required"}, status=401)
    payload = verify_token(auth_header[7:])
    if not payload or payload.get("type") != "access":
        return None, JsonResponse({"detail": "Invalid or expired token"}, status=401)
    user_id = payload.get("user_id")
    if not user_id:
        return None, JsonResponse({"detail": "Invalid or expired token"}, status=401)
    user = User.objects.filter(id=user_id).first()
    if not user:
        return None, JsonResponse({"detail": "User not found"}, status=401)
    if not user.is_active:
        return None, JsonResponse({"detail": "Account is inactive"}, status=401)
    return user, None


def _is_owner_or_admin(user: User, owner_id) -> bool:
    return str(user.id) == str(owner_id) or user.profile == User.ProfileType.ADMIN


def _parse_body(request):
    try:
        return json.loads(request.body), None
    except json.JSONDecodeError:
        return None, JsonResponse({"detail": "Invalid JSON"}, status=400)


def _resolve_offer_type(value):
    if value in (None, ""):
        return None
    try:
        parsed = UUID(str(value))
    except (TypeError, ValueError):
        raise ValueError("Invalid offer_type_id.")
    offer_type = OfferType.objects.filter(id=parsed).first()
    if offer_type is None:
        raise LookupError("Offer type not found.")
    return offer_type


@csrf_exempt
@require_http_methods(["GET", "POST"])
def forum_questions(request):
    if request.method == "GET":
        return _list_questions(request)

    user, err = _require_auth_inline(request)
    if err is not None:
        return err

    data, err = _parse_body(request)
    if err is not None:
        return err

    title = (data.get("title") or "").strip()
    body = (data.get("body") or "").strip()

    if len(title) < TITLE_MIN_LEN:
        return JsonResponse(
            {"detail": f"Title must be at least {TITLE_MIN_LEN} characters."},
            status=400,
        )
    if len(title) > TITLE_MAX_LEN:
        return JsonResponse(
            {"detail": f"Title must be at most {TITLE_MAX_LEN} characters."},
            status=400,
        )
    if len(body) < BODY_MIN_LEN:
        return JsonResponse(
            {"detail": f"Body must be at least {BODY_MIN_LEN} characters."},
            status=400,
        )

    try:
        offer_type = _resolve_offer_type(data.get("offer_type_id"))
    except ValueError as exc:
        return JsonResponse({"detail": str(exc)}, status=400)
    except LookupError as exc:
        return JsonResponse({"detail": str(exc)}, status=404)

    question = ForumQuestion.objects.create(
        title=title,
        body=body,
        author=user,
        offer_type=offer_type,
    )
    return JsonResponse(_question_to_dict(question, answer_count=0), status=201)


def _list_questions(request):
    queryset = (
        ForumQuestion.objects.select_related("author", "offer_type")
        .annotate(answer_count=Count("answers"))
        .order_by("-created_at")
    )

    offer_type_name = request.GET.get("offer_type")
    if offer_type_name:
        queryset = queryset.filter(offer_type__name=offer_type_name)

    search_term = request.GET.get("q")
    if search_term:
        queryset = queryset.filter(
            Q(title__icontains=search_term) | Q(body__icontains=search_term)
        )

    if request.GET.get("mine", "").lower() in ("true", "1", "yes"):
        user = _maybe_authenticated_user(request)
        if user is None:
            return JsonResponse(
                {"detail": "Authentication required for mine filter."},
                status=401,
            )
        queryset = queryset.filter(author=user)

    page_size = _parse_positive_int(
        request.GET.get("page_size"), default=20, max_value=100
    )
    page = _parse_positive_int(
        request.GET.get("page"), default=1, max_value=1000000
    )
    total_count = queryset.count()
    total_pages = ceil(total_count / page_size) if total_count else 0
    offset = (page - 1) * page_size

    rows = list(queryset[offset:offset + page_size])
    results = [_question_to_dict(row, answer_count=row.answer_count) for row in rows]

    return JsonResponse(
        {
            "count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "results": results,
        }
    )


@csrf_exempt
@require_http_methods(["GET", "PATCH", "DELETE"])
def forum_question_detail(request, question_id: str):
    try:
        parsed_id = UUID(question_id)
    except (TypeError, ValueError):
        return JsonResponse({"detail": "Invalid question id."}, status=400)

    question = (
        ForumQuestion.objects.select_related("author", "offer_type")
        .filter(id=parsed_id)
        .first()
    )
    if question is None:
        return JsonResponse({"detail": "Question not found."}, status=404)

    if request.method == "GET":
        answers = list(
            ForumAnswer.objects.select_related("author")
            .filter(question_id=parsed_id)
            .order_by("created_at")
        )
        payload = _question_to_dict(question, answer_count=len(answers))
        payload["answers"] = [_answer_to_dict(a) for a in answers]
        return JsonResponse(payload)

    user, err = _require_auth_inline(request)
    if err is not None:
        return err
    if not _is_owner_or_admin(user, question.author_id):
        return JsonResponse({"detail": "Forbidden."}, status=403)

    if request.method == "DELETE":
        question.delete()
        return JsonResponse({}, status=204)

    data, err = _parse_body(request)
    if err is not None:
        return err

    if "title" in data:
        title = (data.get("title") or "").strip()
        if len(title) < TITLE_MIN_LEN:
            return JsonResponse(
                {"detail": f"Title must be at least {TITLE_MIN_LEN} characters."},
                status=400,
            )
        if len(title) > TITLE_MAX_LEN:
            return JsonResponse(
                {"detail": f"Title must be at most {TITLE_MAX_LEN} characters."},
                status=400,
            )
        question.title = title

    if "body" in data:
        body = (data.get("body") or "").strip()
        if len(body) < BODY_MIN_LEN:
            return JsonResponse(
                {"detail": f"Body must be at least {BODY_MIN_LEN} characters."},
                status=400,
            )
        question.body = body

    if "offer_type_id" in data:
        try:
            question.offer_type = _resolve_offer_type(data.get("offer_type_id"))
        except ValueError as exc:
            return JsonResponse({"detail": str(exc)}, status=400)
        except LookupError as exc:
            return JsonResponse({"detail": str(exc)}, status=404)

    question.save()
    return JsonResponse(_question_to_dict(question))


@csrf_exempt
@require_auth()
@require_http_methods(["POST"])
def forum_answers(request, question_id: str):
    try:
        parsed_id = UUID(question_id)
    except (TypeError, ValueError):
        return JsonResponse({"detail": "Invalid question id."}, status=400)

    question = ForumQuestion.objects.filter(id=parsed_id).first()
    if question is None:
        return JsonResponse({"detail": "Question not found."}, status=404)

    data, err = _parse_body(request)
    if err is not None:
        return err

    body = (data.get("body") or "").strip()
    if len(body) < BODY_MIN_LEN:
        return JsonResponse(
            {"detail": f"Body must be at least {BODY_MIN_LEN} characters."},
            status=400,
        )

    answer = ForumAnswer.objects.create(
        question=question,
        body=body,
        author=request.auth_user,
    )
    return JsonResponse(_answer_to_dict(answer), status=201)


@csrf_exempt
@require_auth()
@require_http_methods(["PATCH", "DELETE"])
def forum_answer_detail(request, answer_id: str):
    try:
        parsed_id = UUID(answer_id)
    except (TypeError, ValueError):
        return JsonResponse({"detail": "Invalid answer id."}, status=400)

    answer = ForumAnswer.objects.select_related("author").filter(id=parsed_id).first()
    if answer is None:
        return JsonResponse({"detail": "Answer not found."}, status=404)

    if not _is_owner_or_admin(request.auth_user, answer.author_id):
        return JsonResponse({"detail": "Forbidden."}, status=403)

    if request.method == "DELETE":
        answer.delete()
        return JsonResponse({}, status=204)

    data, err = _parse_body(request)
    if err is not None:
        return err

    if "body" in data:
        body = (data.get("body") or "").strip()
        if len(body) < BODY_MIN_LEN:
            return JsonResponse(
                {"detail": f"Body must be at least {BODY_MIN_LEN} characters."},
                status=400,
            )
        answer.body = body

    answer.save()
    return JsonResponse(_answer_to_dict(answer))
