import json
from uuid import UUID

from django.db.models import Count, Q
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from content.auth import require_auth
from content.emails import send_approval_email, send_rejection_email
from content.models import (
    AllowedDomain,
    Domain,
    MatchingHit,
    Offer,
    Organization,
    TargetProfile,
    User,
    UserFavorite,
    UserNeed,
    UserOrganization,
    UserProfile,
    UserRole,
)
from content.views._utils import _parse_positive_int

ADMIN_PROFILE = User.ProfileType.ADMIN
DEFAULT_ORGANIZATION_ROLE = "member"
ADMIN_ASSIGNABLE_ORGANIZATION_ROLES = {"member", "contributor", "admin"}

# Maps user profile type to the corresponding TargetProfile name in the DB
_USER_PROFILE_TO_TARGET_PROFILE = {
    "Student": "student",
    "Academic staff": "researcher",
    "Company": "company",
}


def _json_error(error: str, message: str, status: int) -> JsonResponse:
    return JsonResponse({"error": error, "message": message}, status=status)


def _parse_body(request) -> dict | None:
    try:
        return json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return None


def _parse_uuid(value: str, field_name: str) -> UUID | None:
    try:
        return UUID(value)
    except (TypeError, ValueError):
        return None


def _get_user_or_response(user_id: str, request=None) -> tuple[User | None, JsonResponse | None]:
    if user_id == "me":
        auth_user = getattr(request, "auth_user", None)
        if auth_user is None:
            return None, _json_error("authentication_required", "Authentication required.", 401)
        return auth_user, None

    parsed_id = _parse_uuid(user_id, "user_id")
    if parsed_id is None:
        return None, _json_error("validation_error", "Invalid user id.", 400)

    user = User.objects.filter(id=parsed_id).first()
    if user is None:
        return None, _json_error("not_found", "User not found.", 404)

    return user, None


def _is_admin(user: User) -> bool:
    return user.profile == ADMIN_PROFILE


def _require_self_or_admin(request, user: User) -> JsonResponse | None:
    auth_user = getattr(request, "auth_user", None)
    if auth_user is None:
        return _json_error("authentication_required", "Authentication required.", 401)
    if _is_admin(auth_user) or auth_user.id == user.id:
        return None
    return _json_error("forbidden", "You do not have permission to access this user resource.", 403)


def _get_or_create_profile(user: User) -> UserProfile:
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


def _serialize_profile(profile: UserProfile) -> dict:
    return {
        "id": str(profile.id),
        "user_id": str(profile.user_id),
        "bio": profile.bio,
        "avatar_url": profile.avatar_url,
        "preferred_domains": profile.preferred_domains,
        "preferred_countries": profile.preferred_countries,
        "notification_enabled": profile.notification_enabled,
        "created_at": profile.created_at.isoformat(),
        "updated_at": profile.updated_at.isoformat(),
    }


def _serialize_org_link(link: UserOrganization) -> dict:
    return {
        "id": str(link.organization.id),
        "name": link.organization.name,
        "role": link.role.name,
    }


def _serialize_user_detail(user: User) -> dict:
    profile = _get_or_create_profile(user)
    links = list(
        user.organization_links.select_related("organization", "role").order_by("organization__name")
    )
    return {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat(),
        "updated_at": user.updated_at.isoformat(),
        "profile": _serialize_profile(profile),
        "organizations": [_serialize_org_link(link) for link in links],
    }


def _serialize_user_admin(user: User) -> dict:
    """Flat serialization for admin user management — includes approval fields."""
    org_link = UserOrganization.objects.filter(user=user).select_related("organization").first()
    return {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "profile": user.profile,
        "is_active": user.is_active,
        "approval_status": user.approval_status,
        "email_verified": user.email_verified,
        "approved_by": user.approved_by.username if user.approved_by_id else None,
        "approval_notes": user.approval_notes,
        "organization_id": str(org_link.organization.id) if org_link else None,
        "organization_name": org_link.organization.name if org_link else None,
        "created_at": user.created_at.isoformat(),
        "updated_at": user.updated_at.isoformat(),
    }


def _serialize_need(need: UserNeed) -> dict:
    return {
        "id": str(need.id),
        "title": need.title,
        "description": need.description,
        "status": need.status,
        "target_profile_id": str(need.target_profile_id) if need.target_profile_id else None,
        "domain_ids": [str(domain.id) for domain in need.domains.all()],
        "countries": need.countries,
        "matching_hits_count": getattr(need, "matching_hits_count", need.matching_hits.count()),
        "created_at": need.created_at.isoformat(),
        "updated_at": need.updated_at.isoformat(),
    }


def _serialize_offer_preview(offer: Offer) -> dict:
    return {
        "id": str(offer.id),
        "title": offer.title,
        "organization": offer.organization.name,
        "link": offer.link,
    }


def _serialize_favorite(favorite: UserFavorite) -> dict:
    return {
        "id": str(favorite.id),
        "offer": _serialize_offer_preview(favorite.offer),
        "note": favorite.note,
        "created_at": favorite.created_at.isoformat(),
    }


def _serialize_matching_hit(hit: MatchingHit) -> dict:
    return {
        "id": str(hit.id),
        "need": {
            "id": str(hit.need.id),
            "title": hit.need.title,
        },
        "offer": _serialize_offer_preview(hit.offer),
        "match_score": float(hit.match_score),
        "match_reason": hit.match_reason,
        "status": hit.status,
        "created_at": hit.created_at.isoformat(),
        "updated_at": hit.updated_at.isoformat(),
    }


def _paginated_response(request, queryset, serializer, page_size: int, page: int) -> JsonResponse:
    total_count = queryset.count()
    offset = (page - 1) * page_size
    rows = list(queryset[offset:offset + page_size])

    def build_page_url(target_page: int) -> str:
        query = request.GET.copy()
        query["page"] = str(target_page)
        query["page_size"] = str(page_size)
        return request.build_absolute_uri(f"{request.path}?{query.urlencode()}")

    next_url = build_page_url(page + 1) if offset + page_size < total_count else None
    previous_url = build_page_url(page - 1) if page > 1 and total_count else None
    return JsonResponse(
        {
            "count": total_count,
            "next": next_url,
            "previous": previous_url,
            "results": [serializer(row) for row in rows],
        }
    )


def _admin_user_list_response(request) -> JsonResponse:
    page = _parse_positive_int(request.GET.get("page"), default=1, max_value=1000000)
    page_size = _parse_positive_int(request.GET.get("page_size"), default=25, max_value=200)
    search = str(request.GET.get("search") or "").strip()
    status = str(request.GET.get("status") or "").strip()
    approval_status = str(request.GET.get("approval_status") or "").strip()
    profile_filter = str(request.GET.get("profile") or "").strip()

    queryset = User.objects.all().order_by("username")
    if search:
        queryset = queryset.filter(Q(username__icontains=search) | Q(email__icontains=search))
    if status:
        if status not in {"active", "inactive"}:
            return _json_error("validation_error", "status must be active or inactive.", 400)
        queryset = queryset.filter(is_active=(status == "active"))
    if approval_status:
        valid_approval = {s for s, _ in User.ApprovalStatus.choices}
        if approval_status not in valid_approval:
            return _json_error("validation_error", f"approval_status must be one of: {', '.join(valid_approval)}.", 400)
        queryset = queryset.filter(approval_status=approval_status)
    if profile_filter:
        valid_profiles = {p for p, _ in User.ProfileType.choices}
        if profile_filter not in valid_profiles:
            return _json_error("validation_error", f"profile must be one of: {', '.join(valid_profiles)}.", 400)
        queryset = queryset.filter(profile=profile_filter)

    return _paginated_response(request, queryset, _serialize_user_admin, page_size, page)


def _normalize_countries(values) -> list[str]:
    if values is None:
        return []
    if not isinstance(values, list):
        raise ValueError("countries must be a list")
    return [str(value).strip().upper() for value in values if str(value).strip()]


def _resolve_domains(domain_ids) -> list[Domain]:
    if domain_ids is None:
        return []
    if not isinstance(domain_ids, list):
        raise ValueError("domain_ids must be a list")

    parsed_ids: list[UUID] = []
    for value in domain_ids:
        parsed = _parse_uuid(str(value), "domain_id")
        if parsed is None:
            raise ValueError("domain_ids contains an invalid UUID")
        parsed_ids.append(parsed)

    domains = list(Domain.objects.filter(id__in=parsed_ids).order_by("name"))
    if len(domains) != len(parsed_ids):
        raise LookupError("One or more domains were not found.")
    return domains


def _resolve_target_profile(target_profile_id: str) -> TargetProfile:
    parsed_id = _parse_uuid(target_profile_id, "target_profile_id")
    if parsed_id is None:
        raise ValueError("target_profile_id is invalid")

    target_profile = TargetProfile.objects.filter(id=parsed_id).first()
    if target_profile is None:
        raise LookupError("Target profile not found.")
    return target_profile


@require_auth(roles=[ADMIN_PROFILE])
@require_http_methods(["GET"])
def users_collection(request):
    return _admin_user_list_response(request)


@csrf_exempt
@require_auth(roles=[ADMIN_PROFILE])
@require_http_methods(["GET", "PATCH", "DELETE"])
def user_resource(request, user_id: str):
    user, error_response = _get_user_or_response(user_id, request)
    if error_response is not None:
        return error_response

    if request.method == "GET":
        return JsonResponse(_serialize_user_admin(user))

    if request.method == "DELETE":
        user.is_active = False
        user.save(update_fields=["is_active", "updated_at"])
        return JsonResponse({}, status=204)

    body = _parse_body(request)
    if body is None:
        return _json_error("validation_error", "Invalid JSON body.", 400)

    email = body.get("email")
    username = body.get("username")
    is_active = body.get("is_active")
    profile_data = body.get("profile")

    if email is not None:
        normalized_email = str(email).strip().lower()
        if not normalized_email:
            return _json_error("validation_error", "email cannot be blank.", 400)
        if User.objects.exclude(id=user.id).filter(email=normalized_email).exists():
            return _json_error("conflict", "Email is already in use.", 409)
        user.email = normalized_email

    if username is not None:
        normalized_username = str(username).strip()
        if not normalized_username:
            return _json_error("validation_error", "username cannot be blank.", 400)
        if User.objects.exclude(id=user.id).filter(username=normalized_username).exists():
            return _json_error("conflict", "Username is already in use.", 409)
        user.username = normalized_username

    if is_active is not None:
        user.is_active = bool(is_active)

    user.save()

    if profile_data is not None:
        if not isinstance(profile_data, dict):
            return _json_error("validation_error", "profile must be an object.", 400)
        profile = _get_or_create_profile(user)
        if "bio" in profile_data:
            profile.bio = str(profile_data.get("bio") or "")
        if "avatar_url" in profile_data:
            profile.avatar_url = profile_data.get("avatar_url")
        if "preferred_domains" in profile_data:
            profile.preferred_domains = list(profile_data.get("preferred_domains") or [])
        if "preferred_countries" in profile_data:
            profile.preferred_countries = [str(value).upper() for value in profile_data.get("preferred_countries") or []]
        if "notification_enabled" in profile_data:
            profile.notification_enabled = bool(profile_data.get("notification_enabled"))
        profile.save()

    return JsonResponse(_serialize_user_admin(user))


@csrf_exempt
@require_auth(roles=[ADMIN_PROFILE])
@require_http_methods(["PATCH"])
def user_approval(request, user_id: str):
    user, error_response = _get_user_or_response(user_id, request)
    if error_response is not None:
        return error_response

    body = _parse_body(request)
    if body is None:
        return _json_error("validation_error", "Invalid JSON body.", 400)

    action = body.get("action")
    notes = str(body.get("notes") or "").strip()
    email_verified = body.get("email_verified")

    if action == "approve":
        user.is_active = True
        user.approval_status = User.ApprovalStatus.APPROVED
        user.approved_by = request.auth_user
        user.approval_notes = notes
        user.save(update_fields=["is_active", "approval_status", "approved_by", "approval_notes", "updated_at"])
        # Auto-link Teacher to org via AllowedDomain if not already linked
        if user.profile == User.ProfileType.TEACHER:
            domain = user.email.split('@')[-1].lower()
            allowed = AllowedDomain.objects.filter(domain=domain).select_related('organization').first()
            if allowed and not UserOrganization.objects.filter(user=user).exists():
                researcher_role, _ = UserRole.objects.get_or_create(name='researcher', defaults={'description': 'Researcher'})
                UserOrganization.objects.create(user=user, organization=allowed.organization, role=researcher_role)
        send_approval_email(user)
    elif action == "reject":
        user.is_active = False
        user.approval_status = User.ApprovalStatus.REJECTED
        user.approved_by = request.auth_user
        user.approval_notes = notes
        user.save(update_fields=["is_active", "approval_status", "approved_by", "approval_notes", "updated_at"])
        send_rejection_email(user, notes)
    elif action is not None:
        return _json_error("validation_error", "action must be 'approve' or 'reject'.", 400)

    if email_verified is not None:
        user.email_verified = bool(email_verified)
        user.save(update_fields=["email_verified", "updated_at"])

    if action is None and email_verified is None:
        return _json_error("validation_error", "Provide 'action' or 'email_verified'.", 400)

    return JsonResponse(_serialize_user_admin(user))


@csrf_exempt
@require_auth(roles=[ADMIN_PROFILE])
@require_http_methods(["PATCH"])
def user_role(request, user_id: str):
    user, error_response = _get_user_or_response(user_id, request)
    if error_response is not None:
        return error_response

    body = _parse_body(request)
    if body is None:
        return _json_error("validation_error", "Invalid JSON body.", 400)

    new_profile = str(body.get("profile") or "").strip()
    valid_profiles = {p for p, _ in User.ProfileType.choices}
    if not new_profile or new_profile not in valid_profiles:
        return _json_error("validation_error", f"profile must be one of: {', '.join(sorted(valid_profiles))}.", 400)

    user.profile = new_profile
    user.save(update_fields=["profile", "updated_at"])
    return JsonResponse(_serialize_user_admin(user))


@csrf_exempt
@require_auth()
@require_http_methods(["POST"])
def link_user_organization(request, user_id: str):
    user, error_response = _get_user_or_response(user_id, request)
    if error_response is not None:
        return error_response
    authorization_error = _require_self_or_admin(request, user)
    if authorization_error is not None:
        return authorization_error

    body = _parse_body(request)
    if body is None:
        return _json_error("validation_error", "Invalid JSON body.", 400)

    parsed_org_id = _parse_uuid(str(body.get("organization_id", "")), "organization_id")
    if parsed_org_id is None:
        return _json_error("validation_error", "Invalid organization id.", 400)

    organization = Organization.objects.filter(id=parsed_org_id).first()
    if organization is None:
        return _json_error("not_found", "Organization not found.", 404)

    if UserOrganization.objects.filter(user=user, organization=organization).exists():
        return _json_error("conflict", "User is already linked to that organization.", 409)

    requested_role = str(body.get("role") or DEFAULT_ORGANIZATION_ROLE).strip() or DEFAULT_ORGANIZATION_ROLE
    if _is_admin(request.auth_user):
        if requested_role not in ADMIN_ASSIGNABLE_ORGANIZATION_ROLES:
            return _json_error("validation_error", "Invalid organization role.", 400)
        role_name = requested_role
    else:
        if requested_role != DEFAULT_ORGANIZATION_ROLE:
            return _json_error("forbidden", "Only admins can assign organization roles.", 403)
        role_name = DEFAULT_ORGANIZATION_ROLE
    role, _ = UserRole.objects.get_or_create(
        name=role_name,
        defaults={"description": f"{role_name.title()} role"},
    )
    UserOrganization.objects.create(user=user, organization=organization, role=role)
    return JsonResponse({"id": str(organization.id), "name": organization.name, "role": role.name}, status=201)


@csrf_exempt
@require_auth()
@require_http_methods(["DELETE"])
def unlink_user_organization(request, user_id: str, org_id: str):
    user, error_response = _get_user_or_response(user_id, request)
    if error_response is not None:
        return error_response
    authorization_error = _require_self_or_admin(request, user)
    if authorization_error is not None:
        return authorization_error

    parsed_org_id = _parse_uuid(org_id, "org_id")
    if parsed_org_id is None:
        return _json_error("validation_error", "Invalid organization id.", 400)

    deleted, _ = UserOrganization.objects.filter(user=user, organization_id=parsed_org_id).delete()
    if deleted == 0:
        return _json_error("not_found", "Organization link not found.", 404)
    return JsonResponse({}, status=204)


@require_auth()
@require_http_methods(["GET"])
def dashboard(request, user_id: str):
    user, error_response = _get_user_or_response(user_id, request)
    if error_response is not None:
        return error_response
    authorization_error = _require_self_or_admin(request, user)
    if authorization_error is not None:
        return authorization_error

    favorites = list(
        user.favorites.select_related("offer__organization").order_by("-created_at")[:5]
    )
    matches = list(
        user.matching_hits.select_related("need", "offer__organization").order_by("-created_at")[:5]
    )
    payload = {
        "user": _serialize_user_detail(user),
        "stats": {
            "active_needs_count": user.needs.filter(status=UserNeed.NeedStatus.ACTIVE).count(),
            "total_favorites": user.favorites.count(),
            "new_matches_count": user.matching_hits.filter(status=MatchingHit.MatchStatus.NEW).count(),
        },
        "recent_favorites": [_serialize_favorite(favorite) for favorite in favorites],
        "recent_matches": [_serialize_matching_hit(match) for match in matches],
    }
    return JsonResponse(payload)


@csrf_exempt
@require_auth()
@require_http_methods(["GET", "POST"])
def user_needs(request, user_id: str):
    user, error_response = _get_user_or_response(user_id, request)
    if error_response is not None:
        return error_response
    authorization_error = _require_self_or_admin(request, user)
    if authorization_error is not None:
        return authorization_error

    if request.method == "GET":
        status_filter = request.GET.get("status", UserNeed.NeedStatus.ACTIVE)
        valid_statuses = {choice for choice, _ in UserNeed.NeedStatus.choices}
        if status_filter not in valid_statuses:
            return _json_error("validation_error", "Invalid need status filter.", 400)

        page = _parse_positive_int(request.GET.get("page"), default=1, max_value=1000000)
        page_size = _parse_positive_int(request.GET.get("page_size"), default=25, max_value=200)
        queryset = (
            user.needs.filter(status=status_filter)
            .select_related("target_profile")
            .prefetch_related("domains")
            .annotate(matching_hits_count=Count("matching_hits"))
            .order_by("-created_at")
        )
        return _paginated_response(request, queryset, _serialize_need, page_size, page)

    body = _parse_body(request)
    if body is None:
        return _json_error("validation_error", "Invalid JSON body.", 400)

    try:
        target_profile_id_str = str(body.get("target_profile_id") or "").strip()
        if target_profile_id_str:
            target_profile = _resolve_target_profile(target_profile_id_str)
        else:
            tp_name = _USER_PROFILE_TO_TARGET_PROFILE.get(user.profile)
            target_profile = TargetProfile.objects.filter(name=tp_name).first() if tp_name else None
        domains = _resolve_domains(body.get("domain_ids"))
        countries = _normalize_countries(body.get("countries"))
    except ValueError as exc:
        return _json_error("validation_error", str(exc), 400)
    except LookupError as exc:
        return _json_error("not_found", str(exc), 404)

    title = str(body.get("title") or "").strip()
    description = str(body.get("description") or "").strip()
    if not title:
        return _json_error("validation_error", "title is required.", 400)

    need = UserNeed.objects.create(
        user=user,
        title=title,
        description=description,
        target_profile=target_profile,
        countries=countries,
    )
    need.domains.set(domains)
    need = UserNeed.objects.select_related("target_profile").prefetch_related("domains").get(id=need.id)
    return JsonResponse(_serialize_need(need), status=201)


@csrf_exempt
@require_auth()
@require_http_methods(["PUT", "PATCH", "DELETE"])
def user_need_detail(request, user_id: str, need_id: str):
    user, error_response = _get_user_or_response(user_id, request)
    if error_response is not None:
        return error_response
    authorization_error = _require_self_or_admin(request, user)
    if authorization_error is not None:
        return authorization_error

    parsed_need_id = _parse_uuid(need_id, "need_id")
    if parsed_need_id is None:
        return _json_error("validation_error", "Invalid need id.", 400)

    need = (
        UserNeed.objects.filter(id=parsed_need_id, user=user)
        .select_related("target_profile")
        .prefetch_related("domains")
        .first()
    )
    if need is None:
        return _json_error("not_found", "Need not found.", 404)

    if request.method == "DELETE":
        need.delete()
        return JsonResponse({}, status=204)

    body = _parse_body(request)
    if body is None:
        return _json_error("validation_error", "Invalid JSON body.", 400)

    valid_statuses = {choice for choice, _ in UserNeed.NeedStatus.choices}
    status_value = body.get("status", need.status)
    if status_value not in valid_statuses:
        return _json_error("validation_error", "Invalid need status.", 400)

    try:
        target_profile_id_raw = body.get("target_profile_id", need.target_profile_id)
        if target_profile_id_raw is not None:
            target_profile = _resolve_target_profile(str(target_profile_id_raw))
        else:
            target_profile = None
        domains = _resolve_domains(body.get("domain_ids"))
        countries = _normalize_countries(body.get("countries"))
    except ValueError as exc:
        return _json_error("validation_error", str(exc), 400)
    except LookupError as exc:
        return _json_error("not_found", str(exc), 404)

    title = str(body.get("title") or need.title).strip()
    description = str(body.get("description") if "description" in body else need.description).strip()
    if not title:
        return _json_error("validation_error", "title is required.", 400)

    need.title = title
    need.description = description
    need.status = status_value
    need.target_profile = target_profile
    need.countries = countries
    need.save()
    need.domains.set(domains)
    need.refresh_from_db()
    return JsonResponse(_serialize_need(need))


@csrf_exempt
@require_auth()
@require_http_methods(["GET", "POST"])
def user_favorites(request, user_id: str):
    user, error_response = _get_user_or_response(user_id, request)
    if error_response is not None:
        return error_response
    authorization_error = _require_self_or_admin(request, user)
    if authorization_error is not None:
        return authorization_error

    if request.method == "GET":
        page = _parse_positive_int(request.GET.get("page"), default=1, max_value=1000000)
        page_size = _parse_positive_int(request.GET.get("page_size"), default=25, max_value=200)
        queryset = user.favorites.select_related("offer__organization").order_by("-created_at")
        return _paginated_response(request, queryset, _serialize_favorite, page_size, page)

    body = _parse_body(request)
    if body is None:
        return _json_error("validation_error", "Invalid JSON body.", 400)

    parsed_offer_id = _parse_uuid(str(body.get("offer_id", "")), "offer_id")
    if parsed_offer_id is None:
        return _json_error("validation_error", "Invalid offer id.", 400)

    offer = Offer.objects.select_related("organization").filter(id=parsed_offer_id).first()
    if offer is None:
        return _json_error("not_found", "Offer not found.", 404)

    if UserFavorite.objects.filter(user=user, offer=offer).exists():
        return _json_error("conflict", "Offer is already favorited.", 409)

    favorite = UserFavorite.objects.create(
        user=user,
        offer=offer,
        note=str(body.get("note") or ""),
    )
    favorite = UserFavorite.objects.select_related("offer__organization").get(id=favorite.id)
    return JsonResponse(_serialize_favorite(favorite), status=201)


@csrf_exempt
@require_auth()
@require_http_methods(["DELETE"])
def user_favorite_detail(request, user_id: str, offer_id: str):
    user, error_response = _get_user_or_response(user_id, request)
    if error_response is not None:
        return error_response
    authorization_error = _require_self_or_admin(request, user)
    if authorization_error is not None:
        return authorization_error

    parsed_offer_id = _parse_uuid(offer_id, "offer_id")
    if parsed_offer_id is None:
        return _json_error("validation_error", "Invalid offer id.", 400)

    deleted, _ = UserFavorite.objects.filter(user=user, offer_id=parsed_offer_id).delete()
    if deleted == 0:
        return _json_error("not_found", "Favorite not found.", 404)
    return JsonResponse({}, status=204)


@require_auth()
@require_http_methods(["GET"])
def user_matching_hits(request, user_id: str):
    user, error_response = _get_user_or_response(user_id, request)
    if error_response is not None:
        return error_response
    authorization_error = _require_self_or_admin(request, user)
    if authorization_error is not None:
        return authorization_error

    valid_statuses = {choice for choice, _ in MatchingHit.MatchStatus.choices}
    status_filter = request.GET.get("status")
    if status_filter and status_filter not in valid_statuses:
        return _json_error("validation_error", "Invalid match status filter.", 400)

    sort = request.GET.get("sort", "-match_score")
    if sort not in {"-match_score", "created_at"}:
        return _json_error("validation_error", "Invalid matching hit sort.", 400)

    page = _parse_positive_int(request.GET.get("page"), default=1, max_value=1000000)
    page_size = _parse_positive_int(request.GET.get("page_size"), default=25, max_value=200)
    queryset = user.matching_hits.select_related("need", "offer__organization")
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    queryset = queryset.order_by(sort)
    return _paginated_response(request, queryset, _serialize_matching_hit, page_size, page)


@csrf_exempt
@require_auth()
@require_http_methods(["PATCH"])
def user_matching_hit_detail(request, user_id: str, hit_id: str):
    user, error_response = _get_user_or_response(user_id, request)
    if error_response is not None:
        return error_response
    authorization_error = _require_self_or_admin(request, user)
    if authorization_error is not None:
        return authorization_error

    parsed_hit_id = _parse_uuid(hit_id, "hit_id")
    if parsed_hit_id is None:
        return _json_error("validation_error", "Invalid matching hit id.", 400)

    hit = (
        MatchingHit.objects.filter(id=parsed_hit_id, user=user)
        .select_related("need", "offer__organization")
        .first()
    )
    if hit is None:
        return _json_error("not_found", "Matching hit not found.", 404)

    body = _parse_body(request)
    if body is None:
        return _json_error("validation_error", "Invalid JSON body.", 400)

    status_value = body.get("status")
    valid_statuses = {
        MatchingHit.MatchStatus.VIEWED,
        MatchingHit.MatchStatus.INTERESTED,
        MatchingHit.MatchStatus.DECLINED,
    }
    if status_value not in valid_statuses:
        return _json_error("validation_error", "Invalid matching hit status.", 400)

    hit.status = status_value
    if hit.viewed_at is None:
        hit.viewed_at = timezone.now()
    hit.save()
    return JsonResponse(_serialize_matching_hit(hit))
