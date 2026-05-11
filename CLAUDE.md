# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

UniPortal — a "One Stop Shop" web portal for universities. Users (students, academic staff, companies) browse and get matched to opportunities (scholarships, partnerships, internships, etc.) scraped from partner university websites.

Three independently deployable pieces:
- **`frontend/`** — Vue 3 user-facing portal
- **`backend/`** — Django REST API + PostgreSQL
- **`backend/ui/`** — Angular 17 admin dashboard (lives inside the backend folder)

## Commands

### Fastest start: Docker Compose (runs everything)
```bash
# from project root — starts postgres, api, admin-ui, scraper-worker
docker-compose up --build
# API: http://localhost:8000  |  Admin UI: http://localhost:4200
```

Copy `backend/.env.example` → `backend/.env` before first run.

### Frontend (Vue 3, run from `frontend/`)
```bash
npm install
npm run dev      # http://localhost:5173
npm run build
```

### Backend Django API (run from `backend/`)
```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_lookups   # populate lookup tables (offer types, domains, etc.)
python manage.py runserver      # http://localhost:8000
```

### Admin UI (Angular 17, run from `backend/ui/`)
```bash
npm install
npm start        # http://localhost:4200  (proxies API calls to :8000)
npm run build
npm test         # Karma/Jasmine unit tests
```

### Scraper management commands (run from `backend/`)
```bash
# One-off scrape (legacy path)
python manage.py run_scrape_once [--source-key <key>] [--dry-run]

# One-off scrape (queue-based path — preferred)
python manage.py run_scrape_once --queue [--source-key <key>]

# Long-running background worker (used in docker-compose)
python manage.py run_scraper_worker

# Clean stale crawl URL records
python manage.py clean_crawl_junk
```

## Architecture

### Backend Django app (`backend/content/`)

All business logic lives in the single `content` Django app. Key sub-modules:

| Path | What it does |
|---|---|
| `models.py` | All database models (see below) |
| `auth.py` | Custom JWT auth — PBKDF2 password hashing, HS256 access (1 h) + refresh (7 d) tokens |
| `jwt_auth.py` | Token verification helpers used by views |
| `urls.py` | All API routes under `/api/` |
| `views/` | Per-resource view files: `offers.py`, `users.py`, `scraping.py`, `lookups.py`, `imports.py` |
| `scrapers/service.py` | `ScrapeService` — fetches pages, runs deterministic extractors, falls back to Ollama LLM |
| `scrapers/queue_service.py` | Queue-based scrape flow: crawler populates `CrawlUrl`, then batch scraper processes them |
| `scrapers/source_registry.py` | Registry of `SourceDefinition` objects (one per partner university) |
| `scrapers/ollama_client.py` | HTTP client for local Ollama LLM (model: `qwen3-coder:480b-cloud`) |
| `ingestion/importer.py` | CSV bulk-import for offers |
| `seeding.py` | Seed helpers used by management commands |

**API base path:** `POST /api/auth/...`, `GET /api/offers`, `GET /api/users/<id>/dashboard`, etc. — see `content/urls.py` for the full list.

### Data model (key entities)

```
Organization ──< Offer >── OfferType, TargetProfile, Domain
     │
     └──< UserOrganization >── User
                                │
                    ┌───────────┼───────────────┐
                    │           │               │
               UserProfile   UserNeed >── MatchingHit >── Offer
                                │
                           UserFavorite >── Offer

ScrapingJob ──< ScrapingRun
CrawlUrl (tracks per-URL scrape state)
```

All PKs are UUIDs. DB tables live in the `content` Postgres schema (`search_path` set in `settings.py`).

User profiles: `Student`, `Academic staff`, `Company`.

### Authentication flow

Custom JWT (no Django REST Framework or SimpleJWT). Protected views call `verify_token()` from `jwt_auth.py` directly and check `Authorization: Bearer <token>`. Rate limiting via `django-ratelimit` on login/register (5–10 req/h per IP).

### Scraper pipeline

Two modes coexist:

1. **Legacy** (`ScrapeService.run()`): fetches each source's listing page directly, tries deterministic regex/CSS extractors (`extractors.py`), falls back to Ollama if confidence < `SCRAPER_LLM_FALLBACK_THRESHOLD` (default 0.60).

2. **Queue-based** (preferred): `run_crawler()` discovers individual offer URLs and writes them to `CrawlUrl`; then `run_url_scraper_batch()` processes the queue. The `scraper-worker` docker service uses this path.

### Frontend (`frontend/src/`)

Vue 3 with `<script setup>` and no state management library. Entry: `main.js` → `App.vue` (contains `<router-view>`).

Routes (`router/index.js`):
- `/` → `Landing.vue`
- `/home` → `Home.vue`
- `/student`, `/staff`, `/external_user` → role-specific pages
- `/profile_selection`, `/user_profile` → profile flow

Shared shell: `components/layout/AppHeader.vue` + `AppFooter.vue`. Page sections live in `components/sections/`.

### Admin UI (`backend/ui/src/app/`)

Angular 17 SPA. Pages: Dashboard, Offers, Import, Scraper Admin. Shared API service: `shared/oss-api.service.ts`. Served by Nginx in Docker, proxied to the Django API.

## Environment variables

See `backend/.env.example` for all variables. Notable ones:

| Variable | Default | Notes |
|---|---|---|
| `POSTGRES_HOST` | `localhost` | Use `postgres` inside Docker Compose |
| `POSTGRES_SCHEMA` | `content` | Postgres search_path schema |
| `OLLAMA_BASE_URL` | `http://host.docker.internal:11434` | Local Ollama instance |
| `SCRAPER_LLM_FALLBACK_THRESHOLD` | `0.60` | Confidence below this triggers LLM |
| `CORS_ALLOWED_ORIGINS` | `:4200,:5173` | Comma-separated list |
