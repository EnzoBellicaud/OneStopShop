import jwt
import hashlib
import secrets
from datetime import datetime, timedelta
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json

from content.models import User


def hash_password(password: str) -> str:
	"""Hash a password using PBKDF2."""
	salt = secrets.token_hex(16)
	key = hashlib.pbkdf2_hmac(
		'sha256',
		password.encode('utf-8'),
		bytes.fromhex(salt),
		100000,
	)
	return f"{salt}${key.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
	"""Verify a password against its hash."""
	try:
		salt, key = password_hash.split('$')
		new_key = hashlib.pbkdf2_hmac(
			'sha256',
			password.encode('utf-8'),
			bytes.fromhex(salt),
			100000,
		)
		return new_key.hex() == key
	except (ValueError, AttributeError):
		return False


def generate_tokens(user_id: str, username: str) -> dict:
	"""Generate JWT access and refresh tokens."""
	secret_key = settings.SECRET_KEY
	now = datetime.utcnow()

	# Access token: 1 hour validity
	access_payload = {
		'user_id': str(user_id),
		'username': username,
		'type': 'access',
		'iat': now,
		'exp': now + timedelta(hours=1),
	}
	access_token = jwt.encode(access_payload, secret_key, algorithm='HS256')

	# Refresh token: 7 days validity
	refresh_payload = {
		'user_id': str(user_id),
		'username': username,
		'type': 'refresh',
		'iat': now,
		'exp': now + timedelta(days=7),
	}
	refresh_token = jwt.encode(refresh_payload, secret_key, algorithm='HS256')

	return {
		'access_token': access_token,
		'refresh_token': refresh_token,
		'token_type': 'Bearer',
		'expires_in': 3600,
	}


def verify_token(token: str) -> dict | None:
	"""Verify and decode a JWT token."""
	try:
		secret_key = settings.SECRET_KEY
		payload = jwt.decode(token, secret_key, algorithms=['HS256'])
		return payload
	except jwt.InvalidTokenError:
		return None


@csrf_exempt
@require_http_methods(["POST"])
def register(request):
	"""User registration endpoint."""
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

	# Validation
	if not username or len(username) < 3:
		return JsonResponse({'detail': 'Username must be at least 3 characters'}, status=400)

	if not email or '@' not in email:
		return JsonResponse({'detail': 'Invalid email address'}, status=400)

	if not password or len(password) < 8:
		return JsonResponse({'detail': 'Password must be at least 8 characters'}, status=400)

	# Validate profile
	valid_profiles = [choice[0] for choice in User.ProfileType.choices]
	if profile not in valid_profiles:
		return JsonResponse({'detail': f'Profile must be one of: {", ".join(valid_profiles)}'}, status=400)

	# Check if user already exists
	if User.objects.filter(username=username).exists():
		return JsonResponse({'detail': 'Username already exists'}, status=409)

	if User.objects.filter(email=email).exists():
		return JsonResponse({'detail': 'Email already exists'}, status=409)

	# Create user
	try:
		user = User.objects.create(
			username=username,
			email=email,
			password_hash=hash_password(password),
			first_name=first_name,
			last_name=last_name,
			profile=profile,
		)

		tokens = generate_tokens(user.id, user.username)

		return JsonResponse({
			'user': {
				'id': str(user.id),
				'username': user.username,
				'email': user.email,
				'first_name': user.first_name,
				'last_name': user.last_name,
				'profile': user.profile,
			},
			'tokens': tokens,
		}, status=201)
	except Exception as e:
		return JsonResponse({'detail': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def login(request):
	"""User login endpoint."""
	try:
		data = json.loads(request.body)
	except json.JSONDecodeError:
		return JsonResponse({'detail': 'Invalid JSON'}, status=400)

	username = data.get('username', '').strip()
	password = data.get('password', '')

	if not username or not password:
		return JsonResponse({'detail': 'Username and password required'}, status=400)

	# Find user
	user = User.objects.filter(username=username).first()

	if not user or not verify_password(password, user.password_hash):
		return JsonResponse({'detail': 'Invalid credentials'}, status=401)

	tokens = generate_tokens(user.id, user.username)

	return JsonResponse({
		'user': {
			'id': str(user.id),
			'username': user.username,
			'email': user.email,
			'first_name': user.first_name,
			'last_name': user.last_name,
			'profile': user.profile,
		},
		'tokens': tokens,
	}, status=200)


@csrf_exempt
@require_http_methods(["POST"])
def refresh_token(request):
	"""Refresh access token using refresh token."""
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

	# Get fresh user data
	user = User.objects.filter(id=payload['user_id']).first()

	if not user:
		return JsonResponse({'detail': 'User not found'}, status=404)

	tokens = generate_tokens(user.id, user.username)

	return JsonResponse({
		'tokens': tokens,
	}, status=200)


@require_http_methods(["GET"])
def get_current_user(request):
	"""Get current user info from token."""
	auth_header = request.META.get('HTTP_AUTHORIZATION', '')

	if not auth_header.startswith('Bearer '):
		return JsonResponse({'detail': 'Missing or invalid authorization header'}, status=401)

	token = auth_header[7:]
	payload = verify_token(token)

	if not payload or payload.get('type') != 'access':
		return JsonResponse({'detail': 'Invalid token'}, status=401)

	user = User.objects.filter(id=payload['user_id']).first()

	if not user:
		return JsonResponse({'detail': 'User not found'}, status=404)

	return JsonResponse({
		'user': {
			'id': str(user.id),
			'username': user.username,
			'email': user.email,
			'first_name': user.first_name,
			'last_name': user.last_name,
			'profile': user.profile,
		},
	}, status=200)


@csrf_exempt
@require_http_methods(["PATCH"])
def update_user_profile(request):
	"""Update user profile information."""
	auth_header = request.META.get('HTTP_AUTHORIZATION', '')

	if not auth_header.startswith('Bearer '):
		return JsonResponse({'detail': 'Missing or invalid authorization header'}, status=401)

	token = auth_header[7:]
	payload = verify_token(token)

	if not payload or payload.get('type') != 'access':
		return JsonResponse({'detail': 'Invalid token'}, status=401)

	user = User.objects.filter(id=payload['user_id']).first()

	if not user:
		return JsonResponse({'detail': 'User not found'}, status=404)

	try:
		data = json.loads(request.body)
	except json.JSONDecodeError:
		return JsonResponse({'detail': 'Invalid JSON'}, status=400)

	# Update allowed fields
	if 'first_name' in data:
		user.first_name = data['first_name'].strip()

	if 'last_name' in data:
		user.last_name = data['last_name'].strip()

	if 'profile' in data:
		profile = data['profile'].strip()
		valid_profiles = [choice[0] for choice in User.ProfileType.choices]
		if profile not in valid_profiles:
			return JsonResponse({'detail': f'Profile must be one of: {", ".join(valid_profiles)}'}, status=400)
		user.profile = profile

	user.save()

	return JsonResponse({
		'user': {
			'id': str(user.id),
			'username': user.username,
			'email': user.email,
			'first_name': user.first_name,
			'last_name': user.last_name,
			'profile': user.profile,
		},
	}, status=200)


@csrf_exempt
@require_http_methods(["POST"])
def change_password(request):
	"""Change user password."""
	auth_header = request.META.get('HTTP_AUTHORIZATION', '')

	if not auth_header.startswith('Bearer '):
		return JsonResponse({'detail': 'Missing or invalid authorization header'}, status=401)

	token = auth_header[7:]
	payload = verify_token(token)

	if not payload or payload.get('type') != 'access':
		return JsonResponse({'detail': 'Invalid token'}, status=401)

	user = User.objects.filter(id=payload['user_id']).first()

	if not user:
		return JsonResponse({'detail': 'User not found'}, status=404)

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

	# Verify old password
	if not verify_password(old_password, user.password_hash):
		return JsonResponse({'detail': 'Invalid current password'}, status=401)

	# Update password
	user.password_hash = hash_password(new_password)
	user.save()

	return JsonResponse({
		'detail': 'Password changed successfully',
	}, status=200)
