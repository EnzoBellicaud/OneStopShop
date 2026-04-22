# Frontend - Backend Integration Guide

## API Base URLs

- Local dev: `http://localhost:8000/api`
- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`
- Raw OpenAPI spec: `http://localhost:8000/api/openapi.json`

## Stage 0 Goal

Stage 0 publishes the API contract before the user dashboard endpoints exist in the backend. Frontend work can start immediately with mocks that match the documented request and response shapes.

## Current vs Planned Endpoints

- Live today: offers, lookups, scraping telemetry
- Published for frontend-first development: users, dashboard, needs, favorites, matching hits, admin analytics

## User Identification During Stages 2-5

Authentication is intentionally deferred until Stage 6. Until then, user-scoped routes use a UUID path parameter.

Example:

```text
GET /api/users/550e8400-e29b-41d4-a716-446655440000/dashboard
```

Angular service pattern:

```ts
private readonly userId = localStorage.getItem('userId') ?? crypto.randomUUID();

getDashboard() {
  return this.http.get(`${this.apiBaseUrl}/users/${this.userId}/dashboard`);
}
```

## Error Handling Pattern

Success responses return domain objects directly. Error responses should follow this envelope:

```json
{
  "error": "validation_error",
  "message": "Email is required.",
  "details": {
    "email": ["This field is required."]
  }
}
```

Recommended UI behavior:

- `400`: show inline validation messages
- `404`: show empty state or redirect
- `500`: show retry affordance and log details in console/telemetry

## Mocking Guidance

- Build the UI against `backend/ui/src/app/shared/api.models.ts`
- Start with hardcoded fixtures that match the OpenAPI examples and schema names
- Keep pagination fields (`count`, `next`, `previous`, `results`) even in mocked responses so the integration layer does not change later

## Local Backend Smoke Test

Run from `backend/`:

```bash
python manage.py runserver
```

Then verify:

```bash
curl http://localhost:8000/api/openapi.json
curl http://localhost:8000/api/docs
curl http://localhost:8000/api/redoc
```

## Stage 6 Transition

When auth is introduced later:

- frontend route structure should not change
- service method names and response shapes should stay stable
- JWT handling should be additive on top of the existing path-based user scoping
