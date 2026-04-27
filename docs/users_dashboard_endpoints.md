# Users Dashboard Endpoints

Brief reference for the user dashboard endpoints added in the backend.

## Endpoints

```text
POST   /api/users
GET    /api/users/{user_id}
PATCH  /api/users/{user_id}
DELETE /api/users/{user_id}

POST   /api/users/{user_id}/organizations
DELETE /api/users/{user_id}/organizations/{org_id}

GET    /api/users/{user_id}/dashboard

GET    /api/users/{user_id}/needs
POST   /api/users/{user_id}/needs
PUT    /api/users/{user_id}/needs/{need_id}
DELETE /api/users/{user_id}/needs/{need_id}

GET    /api/users/{user_id}/favorites
POST   /api/users/{user_id}/favorites
DELETE /api/users/{user_id}/favorites/{offer_id}

GET    /api/users/{user_id}/matching-hits
PATCH  /api/users/{user_id}/matching-hits/{hit_id}
```

## Purpose

- `POST /api/users`: create or update a user by email and return the full dashboard user payload.
- `GET/PATCH/DELETE /api/users/{user_id}`: read, update, or soft-delete a user.
- Organization endpoints: attach or remove a user-organization link.
- `GET /dashboard`: return dashboard stats, recent favorites, and recent matches.
- Needs endpoints: list, create, update, and delete user needs.
- Favorites endpoints: list, add, and remove saved offers.
- Matching hits endpoints: list recommendations and update match status.

## Implementation

- Routes are declared in `backend/content/urls.py`
- View logic is implemented with Django function-based JSON endpoints in `backend/content/views.py`
- Data is backed by the dashboard models introduced in `backend/content/migrations/0004_user_dashboard_models.py`
- Requests use path-based user scoping: every user resource is nested under `/api/users/{user_id}`.
- Input is validated with small helpers for JSON parsing, UUID parsing, domain validation, country normalization, and paginated responses.
- Responses are built with explicit serializer-style helper functions such as `_user_to_dict`, `_need_to_dict`, `_favorite_to_dict`, and `_matching_hit_to_dict`.
- Frontend support for `http://localhost:4200` was completed by adding trusted CSRF origins in `backend/oss_backend/settings.py` and exempting the JSON write endpoints used by the Angular dashboard.
