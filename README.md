# OneStopShop

The SUNRISE One Stop Shop application.

## Quick Start

```bash
docker compose up -d --build
```

This starts four services: `postgres`, `api`, `scraper-worker`, `admin-ui`.

The API container runs on startup:
1. `python manage.py migrate`
2. `python manage.py seed_lookups`
3. `python manage.py runserver 0.0.0.0:8000`

The scraper worker runs on startup:
1. `python manage.py seed_lookups`
2. `python manage.py run_scraper_worker`

> **Two separate frontends:** This repo contains the **backend admin UI** (Angular, `localhost:4200`) used by internal operators. The **public-facing student/staff frontend** (Vue.js) is a separate application that consumes the unauthenticated offer and lookup APIs — it is not part of this repo's Docker setup.

To rebuild from a clean state:

```bash
docker compose down -v
docker compose up -d --build --wait
```

## Default Credentials

### Admin account (seeded automatically)

| Field | Value |
|-------|-------|
| Username | `admin` |
| Password | `passw0rd` |
| Email | `admin@oss.com` |
| Profile | `Admin` |

> **Production:** set `ADMIN_SEED_PASSWORD` env var before first `seed_lookups` run. The seed command warns if the default password is used.

Admin accounts cannot be created via the public registration endpoint — `profile: "Admin"` is rejected at the API level. Admin access is only available through the seeded account or direct DB creation.

## Local URLs

### API (`localhost:8000`)

| URL | Description |
|-----|-------------|
| `http://localhost:8000/api` | Swagger UI |
| `http://localhost:8000/api/docs` | Swagger UI (alias) |
| `http://localhost:8000/api/openapi.json` | OpenAPI 3 schema |
| `http://localhost:8000/api/health` | Health check |

### Backend admin UI — Angular (`localhost:4200`)

Internal tool for operators. **All routes require login.** Not accessible to end users.

| URL | Who can access | Description |
|-----|---------------|-------------|
| `http://localhost:4200/login` | Everyone | Login page |
| `http://localhost:4200/offers` | Any logged-in user | Browse and search offers |
| `http://localhost:4200/dashboard` | Any logged-in user | User dashboard |
| `http://localhost:4200/admin/scrapper` | Admin only | Scraper telemetry dashboard |
| `http://localhost:4200/admin/import` | Admin only | Bulk offer import |

### Public frontend — Vue.js (`frontend/`)

The student/staff-facing application. Runs independently from `frontend/`, calls the API without authentication.

## API Endpoints

**Authentication**
- `POST /api/auth/register` — register new user (`username`, `password`, `email`, `profile`: `Student|Academic staff|Company`)
- `POST /api/auth/login` — login, returns `access_token` (1h) + `refresh_token` (7d)
- `POST /api/auth/logout` — invalidate session (requires Bearer token)
- `POST /api/auth/refresh` — exchange refresh token for new access token
- `GET /api/auth/me` — current user info (requires Bearer token)
- `PATCH /api/auth/me` — update `first_name`, `last_name`, `profile` (requires Bearer token)
- `POST /api/auth/change-password` — change password (requires Bearer token)

All protected endpoints require `Authorization: Bearer <access_token>` header. Scraping and import endpoints require `profile: Admin`.

**Authentication** _(used by the backend admin UI)_
- `POST /api/auth/register` — register new user (`username`, `password`, `email`, `profile`: `Student|Academic staff|Company`)
- `POST /api/auth/login` — login, returns `access_token` (1h) + `refresh_token` (7d)
- `POST /api/auth/logout` — invalidate session (requires Bearer token)
- `POST /api/auth/refresh` — exchange refresh token for new access token
- `GET /api/auth/me` — current user info (requires Bearer token)
- `PATCH /api/auth/me` — update `first_name`, `last_name`, `profile` (requires Bearer token)
- `POST /api/auth/change-password` — change password (requires Bearer token)

All protected endpoints require `Authorization: Bearer <access_token>` header. Scraping and import endpoints require `profile: Admin`.

**Lookups** _(public — used by both frontends)_
- `GET /api/lookups/offer-types` — OfferType reference data
- `GET /api/lookups/domains` — Domain reference data
- `GET /api/lookups/organizations` — Organization reference data
- `GET /api/lookups/countries` — Countries used by offers

**Offers** _(public — primary API for the public Vue.js frontend)_
- `GET /api/offers` — offer list (`q`, `status`, `offer_type`, `organization`, `target_profile`, `domain`, `country`, `page`, `page_size`, `limit`)
- `GET /api/offers/{offer_id}` — offer detail

**Users / dashboard** _(Bearer token required)_
- `GET /api/users` — admin-only paginated user list (`search`, `status`, `page`, `page_size`)
- `GET /api/users/{user_id}` — admin-only user profile with dashboard preferences and organizations
- `PATCH /api/users/{user_id}` — admin-only user profile update
- `DELETE /api/users/{user_id}` — admin-only soft-delete user
- `POST /api/users/{user_id}/organizations` — admin or authenticated user themself; non-admin users can only link as `member`
- `DELETE /api/users/{user_id}/organizations/{org_id}` — admin or authenticated user themself
- `GET /api/users/{user_id}/dashboard` — admin or authenticated user themself; `{user_id}` may be `me`
- `GET /api/users/{user_id}/needs` — admin or authenticated user themself (`status`, `page`, `page_size`)
- `POST /api/users/{user_id}/needs` — admin or authenticated user themself
- `PUT /api/users/{user_id}/needs/{need_id}` — admin or authenticated user themself
- `DELETE /api/users/{user_id}/needs/{need_id}` — admin or authenticated user themself
- `GET /api/users/{user_id}/favorites` — admin or authenticated user themself (`page`, `page_size`)
- `POST /api/users/{user_id}/favorites` — admin or authenticated user themself
- `DELETE /api/users/{user_id}/favorites/{offer_id}` — admin or authenticated user themself
- `GET /api/users/{user_id}/matching-hits` — admin or authenticated user themself (`status`, `sort`, `page`, `page_size`)
- `PATCH /api/users/{user_id}/matching-hits/{hit_id}` — admin or authenticated user themself

**Import** _(Admin token required — backend admin UI only)_
- `GET /api/offers/import/template` — download `.xlsx` template with dropdown validation
- `POST /api/offers/import/preview` — parse + validate CSV/Excel, no DB writes (multipart `file` field)
- `POST /api/offers/import/confirm` — write confirmed rows to DB (JSON body `{"rows": [...]}`)

**Scraping runs** _(Admin token required — backend admin UI only)_
- `GET /api/scraping/runs` — recent run summaries (`limit`)
- `GET /api/scraping/runs/{run_id}` — run detail with full log

**Scraping telemetry** _(Admin token required — backend admin UI only)_
- `GET /api/scraping/overview?window=24h|7d|30d` — KPI counts + timeline buckets
- `GET /api/scraping/sources/health` — per-source URL queue stats from `CrawlUrl` table
- `GET /api/scraping/llm/stats?window=24h|7d|30d` — extraction method split + confidence averages

## Scraper Architecture

The scraper runs as two decoupled APScheduler jobs inside the `scraper-worker` container:

### Job 1 — Crawler (every 360 min)

Discovers URLs for each configured source and writes them into the `CrawlUrl` queue table.

- Crawl-enabled sources: BFS depth-1 link discovery filtered by include/exclude patterns
- Non-crawl sources: single known URL
- Uses `get_or_create` — existing URLs keep their schedule, archived URLs are not resurrected

### Job 2 — Scraper (every 5 min)

Claims up to `SCRAPER_BATCH_SIZE` (default 10) pending/due URLs from the queue and processes them.

For each URL:

1. Fetch HTML (timeout: `SCRAPER_TIMEOUT_SECONDS`)
2. Run deterministic extraction (BeautifulSoup / JSON-LD / meta / heuristics)
3. For crawl sources: AI relevance check + extraction via Ollama. LLM result wins if confidence ≥ deterministic
4. For non-crawl sources: AI is primary extractor; deterministic is fallback only
5. If content is extractable: upsert offer into DB, link `CrawlUrl.offer`
6. If page is generic or deemed irrelevant: mark URL as **skipped** (not an error)
7. Update `CrawlUrl` status and schedule next check

**Outcome mapping:**

| HTTP result | Consecutive errors | Outcome |
|-------------|-------------------|---------|
| 2xx | — | `done`, next check in 7 days |
| Generic/irrelevant page | — | `done` (skipped), not an error |
| 404 / 410 | — | `archived`; linked offer archived/deleted |
| 5xx / timeout | < 3 | `error`, backoff: 1h → 6h → 24h |
| 5xx / timeout | ≥ 3 | `archived`; linked offer archived |

### URL Status Lifecycle

```
pending → processing → done      (scraped, revisit in 7 days)
                     → archived  (permanent 404/410 or repeated errors)
                     → error     (transient failure, retry with backoff)
```

### What Counts as an Error vs Skipped

- **Error**: HTTP failure (4xx/5xx) or network exception — visible in Errors tab of dashboard
- **Skipped**: Page fetched OK but content rejected (generic homepage title, AI flagged as non-offer) — amber in Runs tab, not an error

## Scraper Dashboard

Part of the **backend admin UI** at `http://localhost:4200/admin/scrapper` — requires Admin login. Live telemetry, auto-refreshes every 30s.

**Tabs:**

| Tab | What it shows |
|-----|--------------|
| Overview | KPI cards (runs, offers created/updated, URLs skipped, errors), bar charts for run activity and errors over 24h/7d/30d, AI vs rules method split |
| Runs | Browsable list of scraping batches with URL-level results table. Rows: green (ok), amber (skipped), red (error) |
| Queue | Per-source CrawlUrl queue health: total URLs, % done, pending/error/archived counts |
| Errors | Real HTTP/network failures across last 50 runs (skipped URLs excluded) |

## Environment Variables

Copy `backend/.env.example` to `backend/.env` and adjust as needed.

### Database

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_DB` | `oss_db` | |
| `POSTGRES_USER` | `oss_user` | |
| `POSTGRES_PASSWORD` | `oss_password` | |
| `POSTGRES_HOST` | `localhost` (local) / `postgres` (compose) | |
| `POSTGRES_PORT` | `5432` | |
| `POSTGRES_SCHEMA` | `content` | |

### API

| Variable | Default | Description |
|----------|---------|-------------|
| `DJANGO_ALLOWED_HOSTS` | `127.0.0.1,localhost,testserver` | |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:4200,http://127.0.0.1:4200` | |
| `API_PORT` | `8000` | |
| `SECRET_KEY` | (set in .env) | Django secret key — also used to sign JWTs. Rotate in production. |
| `ADMIN_SEED_PASSWORD` | `passw0rd` | Password for the seeded `admin` account. Override before first deploy. |

### Scraper

| Variable | Default | Description |
|----------|---------|-------------|
| `CRAWLER_INTERVAL_MINUTES` | `360` | How often the crawler job runs (URL discovery) |
| `SCRAPER_INTERVAL_MINUTES` | `5` | How often the scraper job runs (URL processing) |
| `SCRAPER_BATCH_SIZE` | `10` | URLs processed per scraper job tick |
| `SCRAPER_REVISIT_DAYS` | `7` | Days before a successfully scraped URL is re-queued |
| `SCRAPER_MAX_CONSECUTIVE_ERRORS` | `3` | Errors before a URL is archived |
| `SCRAPER_TIMEOUT_SECONDS` | `30` | HTTP request timeout per URL |
| `SCRAPER_RUN_ON_START` | `true` | Run both jobs immediately at worker startup |
| `SCRAPER_USER_AGENT` | `SUNRISE-OSS-Scraper/1.0` | |
| `INGESTION_BOT_USERNAME` | `ingestion_bot` | DB user for offer upserts |

### Ollama (AI extraction)

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_BASE_URL` | `http://host.docker.internal:11434` | Use `host.docker.internal` on Windows/Mac Docker Desktop |
| `OLLAMA_MODEL` | `qwen3-coder:480b-cloud` | Primary model |
| `OLLAMA_TIMEOUT_SECONDS` | `45` | |
| `OLLAMA_REQUEST_DELAY_SECONDS` | `2` | Delay between Ollama calls |
| `OLLAMA_COOLDOWN_MAX_WAIT_SECONDS` | `65` | Max wait when all models are in cooldown |

If Ollama is not running, AI extraction silently skips and the scraper continues with deterministic extraction only.

## Manual Operations

### Run a single scrape batch now

```bash
docker compose exec api python manage.py run_scrape_once
```

### Run only one source

```bash
docker compose exec api python manage.py run_scrape_once --source-key unibz_master_software_engineering
```

### Dry-run (no DB writes)

```bash
docker compose exec api python manage.py run_scrape_once --dry-run
```

### Watch live logs

```bash
docker compose logs -f scraper-worker
docker compose logs -f api
```

### Inspect queue state

```bash
docker compose exec api python manage.py shell -c "
from content.models import CrawlUrl
from django.db.models import Count
print(CrawlUrl.objects.values('status').annotate(n=Count('id')))
"
```

### Smoke test endpoints

```bash
# Public
curl http://localhost:8000/api/health
curl "http://localhost:8000/api/offers?limit=5"

# Login and capture token
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"passw0rd"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['tokens']['access_token'])")

# Admin-only endpoints (require token)
curl -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/scraping/runs?limit=5"
curl -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/scraping/overview?window=24h"
curl -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/scraping/sources/health"
curl -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/offers/import/template" --output template.xlsx
curl -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/users"
```

## Backend Structure

```
backend/
├── oss_backend/          Django project config (settings, urls, wsgi, asgi)
└── content/              Single Django app — all business logic
    ├── views/            API view package
    │   ├── __init__.py   Re-exports all view functions (urls.py imports from here)
    │   ├── health.py     health, api_docs, openapi_schema
    │   ├── lookups.py    offer_types, domains, organizations, countries
    │   ├── offers.py     offers, offer_detail
    │   ├── users.py      user dashboard profile, needs, favorites, matching hits
    │   ├── scraping.py   scraping_runs, scraping_run_detail, scraping_overview,
    │   │                 scraping_sources_health, scraping_llm_stats
    │   ├── imports.py    import_template, import_preview, import_confirm
    │   ├── _schema.py    OpenAPI spec dict (internal)
    │   └── _utils.py     _WINDOW_DELTAS, _parse_positive_int (internal)
    ├── scrapers/         Crawler + scraper service (APScheduler jobs)
    ├── ingestion/        CSV/Excel import service
    ├── management/       Django management commands (run_scrape_once, seed_lookups)
    ├── auth.py           JWT auth: register, login, logout, refresh, require_auth decorator
    ├── models.py         Offer, Organization, CrawlUrl, ScrapingRun, User, lookups
    ├── urls.py           URL routing (no changes needed when adding views)
    ├── tests.py          API integration tests
    ├── test_auth.py      Auth endpoint tests (register, login, logout, token flow)
    └── test_scraper_service.py  Scraper unit tests
```

## Data Model Highlights

- `Offer` — scraped offer records with organization, type, domains, country
- `User`, `UserProfile`, `UserNeed`, `UserFavorite`, `MatchingHit` — user dashboard profile, saved needs, favorites, and recommendations
- `ScrapingRun` — one record per scraper batch; holds counters and structured JSON log
- `CrawlUrl` — per-URL queue record (status, next check time, consecutive errors, linked offer)

Migrations: `0001` – `0008` (including `CrawlUrl` in `0005`, `User` model in `0006`, Admin profile type in `0008`)

## Authentication Architecture

JWT-based auth using PyJWT (HS256). No Django session framework used.

### Token lifecycle

| Token | TTL | Usage |
|-------|-----|-------|
| `access_token` | 1 hour | Sent as `Authorization: Bearer <token>` on every API request |
| `refresh_token` | 7 days | Sent to `POST /api/auth/refresh` to get a new access token |

### `require_auth` decorator

Applied to protected views in `content/auth.py`:

```python
@csrf_exempt
@require_auth(roles=['Admin'])   # omit roles= for any authenticated user
@require_http_methods(["GET"])
def my_view(request):
    user = request.auth_user     # verified User instance attached here
    ...
```

Decorator order matters: `@csrf_exempt` outermost, `@require_auth()` second, `@require_http_methods` innermost.

### User profiles

| Profile | Registration | Scraper/Import access |
|---------|-------------|----------------------|
| `Student` | Public | No |
| `Academic staff` | Public | No |
| `Company` | Public | No |
| `Admin` | Seeded only | Yes |

### Backend admin UI auth (Angular)

The Angular app (`localhost:4200`) is an **internal tool** — all routes are gated behind login. End users never interact with it.

- `AuthService` caches `currentUser` and `loggedIn` as properties (no localStorage reads on change detection)
- `AuthInterceptor` attaches `Authorization: Bearer <token>` to every outgoing HTTP request
- On 401 response: `forceLogout()` clears session and redirects to `/login`
- Route guards: `authGuard` (all app pages), `guestGuard` (`/login` redirects logged-in users to `/dashboard`)

### Public Vue.js frontend (`frontend/`)

The public-facing student/staff app lives in `frontend/` in this repo. It calls `GET /api/offers` and `GET /api/lookups/*` without any authentication — those endpoints are intentionally public.

## Source Configuration

Sources are defined in `backend/content/scrapers/source_registry.py`.

Each source specifies:
- URL, organization, offer type, country
- `crawl_enabled` — whether BFS discovery runs or a single known URL is used
- `crawl_match_patterns` / `crawl_exclude_patterns` — URL filters for crawl mode
- `llm_fallback_enabled` — whether Ollama is used for this source

## Seed Data

- `backend/seed_data/task2/OSS_Mapping_Seed.json` — lookups (offer types, domains, organizations)
- `backend/seed_data/task3/OSS_Sample_Offers.json` — illustrative offer records (excludes fictional Task 3 placeholders)
