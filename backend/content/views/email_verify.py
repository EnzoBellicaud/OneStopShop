from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET"])
def verify_email(request: HttpRequest) -> JsonResponse:
    """
    Placeholder endpoint for email verification.
    Returns 501 until the token generation mechanism is implemented.
    Exists now so future frontend links resolve instead of 404-ing.
    """
    return JsonResponse(
        {
            "error": "not_configured",
            "message": "Email verification is not yet available. Contact an admin to verify your email.",
        },
        status=501,
    )
