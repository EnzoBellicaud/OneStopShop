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
| `LLM_ENABLED` | `true` | Enable or disable the Ollama LLM |
| `SCRAPER_CLASSIFIER_THRESHOLD` | `0.15` | Minimum cosine similarity score for the TF-IDF fallback to accept a classification |

### Adding or updating offer types

Offer types are managed via the database (`OfferType` table). Add or edit them using the Django admin or the `seed_lookups` management command. The classifier automatically picks up changes — the catalog is cached for 5 minutes and invalidated whenever an `OfferType` record is saved or deleted.

### Why dynamic classification?

Previously each scraping source had a static `offer_type` field set at configuration time. This caused two problems:

- A single university site may list theses, internships, and courses on the same domain — a fixed type would misclassify most of them.
- Adding a new offer type to the database had no effect on content already being scraped.

Dynamic classification solves both: the type is decided per-offer at runtime based on the actual page content.
