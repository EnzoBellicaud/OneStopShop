import hmac
import hashlib
import json
import secrets
from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django_ratelimit.decorators import ratelimit

from content.models import User

REGISTERABLE_PROFILES = [
	User.ProfileType.STUDENT,
	User.ProfileType.ACADEMIC_STAFF,
	User.ProfileType.COMPANY,
]


def hash_password(password: str) -> str:
	salt = secrets.token_hex(16)
	key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), bytes.fromhex(salt), 100000)
	return f"{salt}${key.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
	try:
		salt, key = password_hash.split('$')
		new_key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), bytes.fromhex(salt), 100000)
		return hmac.compare_digest(new_key.hex(), key)
	except (ValueError, AttributeError):
		return False


def generate_tokens(user_id: str, username: str, profile: str) -> dict:
	secret_key = settings.SECRET_KEY
	now = datetime.now(tz=timezone.utc)

	access_payload = {
		'user_id': str(user_id),
		'username': username,
		'profile': profile,
		'type': 'access',
		'iat': now,
		'exp': now + timedelta(hours=1),
	}
	refresh_payload = {
		'user_id': str(user_id),
		'username': username,
		'type': 'refresh',
		'iat': now,
		'exp': now + timedelta(days=7),
	}
	return {
		'access_token': jwt.encode(access_payload, secret_key, algorithm='HS256'),
		'refresh_token': jwt.encode(refresh_payload, secret_key, algorithm='HS256'),
		'token_type': 'Bearer',
		'expires_in': 3600,
	}


def verify_token(token: str) -> dict | None:
	try:
		return jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
	except jwt.InvalidTokenError:
		return None


def require_auth(roles: list[str] | None = None):
	"""
	Decorator for authentication + optional role-based authorization.

	Usage:
	    @require_auth()                        # any authenticated user
	    @require_auth(roles=['Admin'])         # admin only
	    @require_auth(roles=['Student', 'Company'])  # multiple allowed roles

	Attaches verified User instance to request.auth_user.
	Returns 401 for missing/invalid/expired token or inactive account.
	Returns 403 for insufficient role.

	Decorator ordering: place @csrf_exempt outermost, then @require_auth(),
	then @ratelimit/@require_http_methods innermost. Example:
	    @csrf_exempt
	    @require_auth(roles=['Admin'])
	    @require_http_methods(["POST"])
	    def my_view(request): ...
	"""
	def decorator(view_func):
		@wraps(view_func)
		def wrapper(request, *args, **kwargs):
			auth_header = request.META.get('HTTP_AUTHORIZATION', '')
			if not auth_header.startswith('Bearer '):
				return JsonResponse({'detail': 'Authentication required'}, status=401)

			payload = verify_token(auth_header[7:])
			if not payload or payload.get('type') != 'access':
				return JsonResponse({'detail': 'Invalid or expired token'}, status=401)

			user = User.objects.filter(id=payload['user_id']).first()
			if not user:
				return JsonResponse({'detail': 'User not found'}, status=401)
			if not user.is_active:
				return JsonResponse({'detail': 'Account is inactive'}, status=401)
			if roles and user.profile not in roles:
				return JsonResponse({'detail': 'Insufficient permissions'}, status=403)

			request.auth_user = user
			return view_func(request, *args, **kwargs)
		return wrapper
	return decorator


def _user_dict(user: User) -> dict:
	return {
		'id': str(user.id),
		'username': user.username,
		'email': user.email,
		'first_name': user.first_name,
		'last_name': user.last_name,
		'profile': user.profile,
		'is_active': user.is_active,
	}


@csrf_exempt
@ratelimit(key='ip', rate='5/h', method='POST')
@require_http_methods(["POST"])
def register(request):
	try:
		data = json.loads(request.body)
	except json.JSONDecodeError:
		return JsonResponse({'detail': 'Invalid JSON'}, status=400)

	username = data.get('username', '').strip()
	email = data.get('email', '').strip()
	password = data.get('password', '')
	first_name = data.get('first_name', '').strip()
	last_name = data.get('last_name', '').strip()
	profile = data.get('profile', User.ProfileType.STUDENT).strip()

	if not username or len(username) < 3:
		return JsonResponse({'detail': 'Username must be at least 3 characters'}, status=400)
	if not email or '@' not in email:
		return JsonResponse({'detail': 'Invalid email address'}, status=400)
	if not password or len(password) < 8:
		return JsonResponse({'detail': 'Password must be at least 8 characters'}, status=400)
	if profile not in REGISTERABLE_PROFILES:
		return JsonResponse({'detail': f'Profile must be one of: {", ".join(REGISTERABLE_PROFILES)}'}, status=400)
	if User.objects.filter(username=username).exists():
		return JsonResponse({'detail': 'Username already exists'}, status=409)
	if User.objects.filter(email=email).exists():
		return JsonResponse({'detail': 'Email already exists'}, status=409)

	try:
		user = User.objects.create(
			username=username,
			email=email,
			password_hash=hash_password(password),
			first_name=first_name,
			last_name=last_name,
			profile=profile,
		)
		return JsonResponse({'user': _user_dict(user), 'tokens': generate_tokens(user.id, user.username, user.profile)}, status=201)
	except Exception as e:
		return JsonResponse({'detail': str(e)}, status=500)


@csrf_exempt
@ratelimit(key='ip', rate='10/h', method='POST')
@require_http_methods(["POST"])
def login(request):
	try:
		data = json.loads(request.body)
	except json.JSONDecodeError:
		return JsonResponse({'detail': 'Invalid JSON'}, status=400)

	username = data.get('username', '').strip()
	password = data.get('password', '')

	if not username or not password:
		return JsonResponse({'detail': 'Username and password required'}, status=400)

	user = User.objects.filter(username=username).first()
	if not user or not verify_password(password, user.password_hash):
		return JsonResponse({'detail': 'Invalid credentials'}, status=401)
	if not user.is_active:
		return JsonResponse({'detail': 'Account is inactive'}, status=401)

	return JsonResponse({'user': _user_dict(user), 'tokens': generate_tokens(user.id, user.username, user.profile)}, status=200)


@csrf_exempt
@ratelimit(key='ip', rate='20/h', method='POST')
@require_http_methods(["POST"])
def refresh_token(request):
	try:
		data = json.loads(request.body)
	except json.JSONDecodeError:
		return JsonResponse({'detail': 'Invalid JSON'}, status=400)

	refresh_token_str = data.get('refresh_token', '')
	if not refresh_token_str:
		return JsonResponse({'detail': 'Refresh token required'}, status=400)

	payload = verify_token(refresh_token_str)
	if not payload or payload.get('type') != 'refresh':
		return JsonResponse({'detail': 'Invalid refresh token'}, status=401)

	user = User.objects.filter(id=payload['user_id']).first()
	if not user:
		return JsonResponse({'detail': 'User not found'}, status=404)
	if not user.is_active:
		return JsonResponse({'detail': 'Account is inactive'}, status=401)

	return JsonResponse({'tokens': generate_tokens(user.id, user.username, user.profile)}, status=200)


@require_http_methods(["GET"])
@require_auth()
def get_current_user(request):
	return JsonResponse({'user': _user_dict(request.auth_user)}, status=200)


@csrf_exempt
@require_auth()
@require_http_methods(["PATCH"])
def update_user_profile(request):
	try:
		data = json.loads(request.body)
	except json.JSONDecodeError:
		return JsonResponse({'detail': 'Invalid JSON'}, status=400)

	user = request.auth_user

	if 'first_name' in data:
		user.first_name = data['first_name'].strip()
	if 'last_name' in data:
		user.last_name = data['last_name'].strip()
	if 'profile' in data:
		new_profile = data['profile'].strip()
		if new_profile not in REGISTERABLE_PROFILES:
			return JsonResponse({'detail': f'Profile must be one of: {", ".join(REGISTERABLE_PROFILES)}'}, status=400)
		user.profile = new_profile

	user.save()
	return JsonResponse({'user': _user_dict(user)}, status=200)


@csrf_exempt
@require_auth()
@ratelimit(key='ip', rate='5/h', method='POST')
@require_http_methods(["POST"])
def change_password(request):
	try:
		data = json.loads(request.body)
	except json.JSONDecodeError:
		return JsonResponse({'detail': 'Invalid JSON'}, status=400)

	old_password = data.get('old_password', '')
	new_password = data.get('new_password', '')

	if not old_password or not new_password:
		return JsonResponse({'detail': 'Old and new passwords required'}, status=400)
	if len(new_password) < 8:
		return JsonResponse({'detail': 'New password must be at least 8 characters'}, status=400)

	user = request.auth_user
	if not verify_password(old_password, user.password_hash):
		return JsonResponse({'detail': 'Invalid current password'}, status=401)

	user.password_hash = hash_password(new_password)
	user.save()
	return JsonResponse({'detail': 'Password changed successfully'}, status=200)


@csrf_exempt
@require_http_methods(["POST"])
def logout(request):
	return JsonResponse({'detail': 'Logged out successfully'}, status=200)
