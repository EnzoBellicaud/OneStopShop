# Authentication API Documentation

## Overview
The OneStopShop backend provides JWT-based authentication for user registration, login, and profile management.

## Base URL
```
http://localhost:8000/api
```

## Authentication
Most endpoints require Bearer token authentication:
```
Authorization: Bearer <access_token>
```

---

## Endpoints

### 1. User Registration
**POST** `/auth/register`

Create a new user account.

**Request Body:**
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "secure_password_123",
  "first_name": "John",
  "last_name": "Doe",
  "profile": "Student"
}
```

**Parameters:**
- `username` (string, required): 3-150 characters, must be unique
- `email` (string, required): Valid email, must be unique
- `password` (string, required): Minimum 8 characters
- `first_name` (string, optional): User's first name
- `last_name` (string, optional): User's last name
- `profile` (string, optional): One of `"Student"`, `"Academic staff"`, `"Company"` (default: `"Student"`)

**Success Response (201):**
```json
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "john_doe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "profile": "Student"
  },
  "tokens": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "token_type": "Bearer",
    "expires_in": 3600
  }
}
```

**Error Responses:**
- `400`: Invalid input (username too short, weak password, etc.)
- `409`: Username or email already exists

---

### 2. User Login
**POST** `/auth/login`

Authenticate a user and receive tokens.

**Request Body:**
```json
{
  "username": "john_doe",
  "password": "secure_password_123"
}
```

**Parameters:**
- `username` (string, required): Username or email
- `password` (string, required): User's password

**Success Response (200):**
```json
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "john_doe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "profile": "Student"
  },
  "tokens": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "token_type": "Bearer",
    "expires_in": 3600
  }
}
```

**Error Responses:**
- `400`: Missing username or password
- `401`: Invalid credentials

---

### 3. Refresh Access Token
**POST** `/auth/refresh`

Get a new access token using a refresh token.

**Request Body:**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Parameters:**
- `refresh_token` (string, required): Valid refresh token from login

**Success Response (200):**
```json
{
  "tokens": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "token_type": "Bearer",
    "expires_in": 3600
  }
}
```

**Error Responses:**
- `400`: Missing refresh token
- `401`: Invalid or expired refresh token

---

### 4. Get Current User
**GET** `/auth/me`

Retrieve information about the authenticated user.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Success Response (200):**
```json
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "john_doe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "profile": "Student"
  }
}
```

**Error Responses:**
- `401`: Missing or invalid token
- `404`: User not found

---

### 5. Update User Profile
**PATCH** `/auth/me/update`

Update user profile information (name and profile type).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "first_name": "Jonathan",
  "last_name": "Smith",
  "profile": "Academic staff"
}
```

**Parameters:**
- `first_name` (string, optional): Updated first name
- `last_name` (string, optional): Updated last name
- `profile` (string, optional): One of `"Student"`, `"Academic staff"`, `"Company"`

**Success Response (200):**
```json
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "john_doe",
    "email": "john@example.com",
    "first_name": "Jonathan",
    "last_name": "Smith",
    "profile": "Academic staff"
  }
}
```

**Error Responses:**
- `400`: Invalid profile type
- `401`: Missing or invalid token
- `404`: User not found

---

### 6. Change Password
**POST** `/auth/change-password`

Change the authenticated user's password.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "old_password": "secure_password_123",
  "new_password": "new_secure_password_456"
}
```

**Parameters:**
- `old_password` (string, required): Current password
- `new_password` (string, required): New password (minimum 8 characters)

**Success Response (200):**
```json
{
  "detail": "Password changed successfully"
}
```

**Error Responses:**
- `400`: Missing passwords or new password too short
- `401`: Invalid current password or missing/invalid token
- `404`: User not found

---

## Token Details

### Access Token
- **Validity**: 1 hour
- **Usage**: Include in `Authorization: Bearer <token>` header
- **Type**: HS256 JWT
- **Claims**: user_id, username, type, iat, exp

### Refresh Token
- **Validity**: 7 days
- **Usage**: Use with `/auth/refresh` endpoint to get new access token
- **Type**: HS256 JWT
- **Claims**: user_id, username, type, iat, exp

---

## Password Requirements
- Minimum 8 characters
- Must contain uppercase, lowercase, and numbers (recommended)

## User Profiles
- `Student`: Default profile for student users
- `Academic staff`: For university staff and faculty
- `Company`: For company/organization representatives

---

## Example Workflow

### 1. Register a new user
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "jane_doe",
    "email": "jane@example.com",
    "password": "SecurePass123",
    "first_name": "Jane",
    "last_name": "Doe",
    "profile": "Student"
  }'
```

### 2. Login
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "jane_doe",
    "password": "SecurePass123"
  }'
```

### 3. Get current user with access token
```bash
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

### 4. Update profile
```bash
curl -X PATCH http://localhost:8000/api/auth/me/update \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..." \
  -d '{
    "first_name": "Janice",
    "profile": "Academic staff"
  }'
```

### 5. Change password
```bash
curl -X POST http://localhost:8000/api/auth/change-password \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..." \
  -d '{
    "old_password": "SecurePass123",
    "new_password": "NewSecurePass456"
  }'
```

### 6. Refresh access token
```bash
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }'
```

---

## Security Considerations

1. **Token Storage**: Store tokens securely (httpOnly cookies or secure storage)
2. **HTTPS**: Always use HTTPS in production
3. **Token Expiration**: Access tokens expire after 1 hour; refresh tokens after 7 days
4. **Password Hashing**: Passwords are hashed using PBKDF2 with SHA256
5. **CSRF Protection**: CSRF protection is enabled (except for auth endpoints)
6. **Rate Limiting**: Recommended to implement rate limiting for auth endpoints

