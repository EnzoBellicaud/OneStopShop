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
