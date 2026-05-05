"""JWT authentication middleware and utilities."""
import jwt
from functools import wraps
from django.http import JsonResponse
from django.conf import settings
from content.models import User


def get_user_from_token(request):
	"""Extract and verify user from Authorization header."""
	auth_header = request.META.get('HTTP_AUTHORIZATION', '')

	if not auth_header.startswith('Bearer '):
		return None

	token = auth_header[7:]

	try:
		secret_key = settings.SECRET_KEY
		payload = jwt.decode(token, secret_key, algorithms=['HS256'])
		if payload.get('type') != 'access':
			return None

		user = User.objects.filter(id=payload['user_id']).first()
		return user
	except jwt.InvalidTokenError:
		return None


def require_token_auth(view_func):
	"""Decorator to require JWT token authentication."""
	@wraps(view_func)
	def wrapped_view(request, *args, **kwargs):
		user = get_user_from_token(request)
		if not user:
			return JsonResponse({'detail': 'Unauthorized'}, status=401)

		request.user = user
		return view_func(request, *args, **kwargs)

	return wrapped_view
