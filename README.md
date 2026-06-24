# UniPortal — One Stop Shop

A university portal where students, academic staff, and companies browse and get matched to opportunities (scholarships, internships, research groups, partnerships) scraped from partner university websites.

---

## Quick Start (Docker — recommended)

Runs everything: database, API, admin UI, and scraper worker.

### Requirements
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- [Node.js](https://nodejs.org/) (for the Vue frontend)

### Step 1 — Copy the environment file
```bash
copy backend\.env.example backend\.env
```

### Step 2 — Start all backend services
From the project root:
```bash
docker-compose up --build
```
Wait until you see the API is healthy (about 1–2 minutes).

### Step 3 — Set up the database (first run only)
Open a new terminal in the project root:
```bash
docker-compose exec api python manage.py migrate
docker-compose exec api python manage.py seed_lookups
```

### Step 4 — Start the frontend
Open another terminal:
```bash
cd frontend
npm install
npm run dev
```

### Step 5 — Open in browser

| Service | URL |
|---|---|
| **Frontend (Vue)** | http://localhost:5173 |
| **API** | http://localhost:8000 |
| **Admin UI** | http://localhost:4200 |

---

## Populate offers (scraper)

Offers are scraped from partner university websites. Run the scraper manually:
```bash
docker-compose exec api python manage.py run_scrape_once --queue
```
Or check the scraper worker logs (it runs automatically in the background):
```bash
docker-compose logs scraper-worker
```

---

## Scraper & Crawler Architecture

The scraper worker runs two independent loops in parallel background threads:

### CrawlerService — discovery loop

Runs every `CRAWLER_INTERVAL_SECONDS` (default: 1s).

1. BFS-crawls the source listing page to collect all live offer URLs.
2. Creates a `CrawlUrl` record (status `PENDING`) for any new URL found.
3. **Deletion detection** — any `CrawlUrl` no longer present in the live listing is bumped to `next_check_at = now`, so the scraper re-fetches it immediately and detects the 404.
4. **Manual offer cleanup** — offers created manually in the admin (no `CrawlUrl`) whose link matches the source domain but is absent from the live listing are HEAD-checked directly; those returning 404/410 are archived.

### UrlScraperService — scrape loop

Runs every `SCRAPER_INTERVAL_SECONDS` (default: 1s).

1. Claims all `CrawlUrl` records where `next_check_at <= now`.
2. Fetches each URL (timeout: `SCRAPER_TIMEOUT_SECONDS`, default: 1s).
3. **4xx response** → offer is immediately archived (`PUBLISHED`/`DRAFT` → `ARCHIVED`).
4. **5xx response** → transient error; exponential backoff applied, retried later.
5. **200 with empty/generic page** → if a linked offer exists, it is archived; otherwise the URL is skipped.
6. **200 with valid content** → offer is created or updated.

### Archiving behaviour

Offers are **never hard-deleted** from the database. All removal triggers result in `status = ARCHIVED`. Archived offers are hidden from the public Vue frontend but remain visible in the admin dashboard.

| Trigger | Result |
|---|---|
| URL returns 4xx (404, 410, etc.) | ARCHIVED immediately |
| URL returns 5xx | Backoff, retried later |
| URL returns 200 but page is empty/generic | ARCHIVED (if offer linked) |
| URL disappears from source listing | CrawlUrl bumped → re-fetched → 404 → ARCHIVED |
| Manually created offer URL gone from listing | HEAD-checked → 404/410 → ARCHIVED |

### Scraper worker configuration

| Variable | Default | Description |
|---|---|---|
| `CRAWLER_INTERVAL_SECONDS` | `1` | How often the crawler discovery loop runs |
| `SCRAPER_INTERVAL_SECONDS` | `1` | How often the scraper drain loop runs |
| `SCRAPER_TIMEOUT_SECONDS` | `1` | HTTP request timeout per URL |

### LLM extraction

Each scraped page is processed by one of two extraction methods:

- **Ollama LLM (primary)** — structured JSON extraction with offer type classification. Configured per source in the admin panel.
- **Deterministic fallback** — `<meta name="description">` as summary; TF-IDF cosine similarity for offer type classification. Used automatically when Ollama is not running or returns a connection error (no wait, no cooldown).

---

## Useful Docker commands

```bash
docker-compose ps                   # check status of all containers
docker-compose logs api             # view API logs
docker-compose logs scraper-worker  # view scraper logs
docker-compose down                 # stop everything
docker-compose up                   # start without rebuilding
docker-compose up --build           # rebuild and start
```

---

## Manual Setup (without Docker)

### Backend (Django API)

From `backend/`:
```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Mac/Linux
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_lookups
python manage.py runserver      # http://localhost:8000
```

### Frontend (Vue 3)

From `frontend/`:
```bash
npm install
npm run dev                     # http://localhost:5173
```

### Admin UI (Angular 17)

From `backend/ui/`:
```bash
npm install
npm start                       # http://localhost:4200
```

---

## Project Structure

```
OneStopShop/
├── frontend/          # Vue 3 user portal
├── backend/           # Django REST API + PostgreSQL
│   ├── content/       # Main Django app (models, views, scrapers)
│   ├── ui/            # Angular 17 admin dashboard
│   └── docker/        # Dockerfiles for api and ui
└── docker-compose.yml
```

## User Roles

| Role | URL | Description |
|---|---|---|
| Student | /student | Browse thesis and training opportunities |
| Academic Staff | /staff | Browse research groups and funding |
| External / Company | /external_user | Browse funding partners and research groups |

---

## Offer Type Classification

Each scraped offer is automatically classified into one of the offer types stored in the database (thesis, internship, scholarship, etc.). Classification happens at scrape time — there is no static type assigned to a source.

### How it works

1. **LLM (primary)** — When the Ollama LLM is enabled, the relevance prompt includes all current offer types and their descriptions from the database. The LLM returns the best matching type as part of its structured JSON response.

2. **TF-IDF cosine similarity (deterministic fallback)** — When the LLM is disabled (`LLM_ENABLED=false`) or returns no type, the scraper falls back to a deterministic classifier. It builds a TF-IDF vector space from the names and descriptions of all offer types, then computes cosine similarity between the extracted offer title+summary and each type. The highest-scoring type is selected if it exceeds the confidence threshold.

3. **Discard** — If neither method can confidently classify the offer, it is discarded. This prevents incorrectly typed offers from appearing in the portal.

### Configuration

| Variable | Default | Description |
|---|---|---|
| `LLM_ENABLED` | `true` | Enable or disable the Ollama LLM globally |
| `SCRAPER_CLASSIFIER_THRESHOLD` | `0.15` | Minimum cosine similarity score for the TF-IDF fallback to accept a classification |
| `CRAWLER_INTERVAL_SECONDS` | `1` | Crawler discovery loop interval |
| `SCRAPER_INTERVAL_SECONDS` | `1` | Scraper drain loop interval |
| `SCRAPER_TIMEOUT_SECONDS` | `1` | HTTP request timeout per scraped URL |

### Adding or updating offer types

Offer types are managed via the database (`OfferType` table). Add or edit them using the Django admin or the `seed_lookups` management command. The classifier automatically picks up changes — the catalog is cached for 5 minutes and invalidated whenever an `OfferType` record is saved or deleted.

### Why dynamic classification?

Previously each scraping source had a static `offer_type` field set at configuration time. This caused two problems:

- A single university site may list theses, internships, and courses on the same domain — a fixed type would misclassify most of them.
- Adding a new offer type to the database had no effect on content already being scraped.

Dynamic classification solves both: the type is decided per-offer at runtime based on the actual page content.
