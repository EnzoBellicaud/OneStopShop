# How to Start the Project with Docker

## Requirements

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- No other service using ports **5432**, **8000**, or **4200**

---

## Step 1 — Start all services

Open a terminal in the project root folder (where `docker-compose.yml` is) and run:

```bash
docker-compose up --build
```

This starts 4 containers:
- **oss-postgres** — PostgreSQL database
- **oss-api** — Django REST API on http://localhost:8000
- **oss-ui** — Angular admin panel on http://localhost:4200
- **oss-scraper-worker** — background scraper worker

The first run takes a few minutes to build. Migrations and seed data run automatically.

Wait until you see the API container log:
```
Starting development server at http://0.0.0.0:8000/
```

---

## Step 2 — Create an admin user (first time only)

Open a **second terminal** while Docker is running:

```bash
docker exec oss-api python manage.py shell -c "
from content.models import User
from content.auth import hash_password
User.objects.create(username='admin', email='admin@example.com', password_hash=hash_password('admin123'), profile='Admin', is_active=True)
print('Admin user created')
"
```

---

## Step 3 — Open in browser

| Page | URL | Credentials |
|---|---|---|
| Admin panel (Angular) | http://localhost:4200 | `admin` / `admin123` |
| API documentation | http://localhost:8000/api/docs | — |
| API health check | http://localhost:8000/api/health | — |

---

## Step 4 — Start the Vue frontend (optional)

The public-facing website is not included in Docker Compose. To run it, open a terminal in the `frontend/` folder:

```bash
cd frontend
npm install
npm run dev
```

Then open http://localhost:5173

---

## Stopping

```bash
# Stop all containers (keeps the database data)
docker-compose down

# Stop and delete all data (full reset)
docker-compose down -v
```

---

## Restarting after changes

```bash
docker-compose up --build
```

---

## Troubleshooting

**Port already in use** — another app is using port 8000, 4200, or 5432. Stop the conflicting app or change the port in `.env`:
```
API_PORT=8001
UI_PORT=4201
```

**Admin user already exists error** — the user was already created in a previous run. You can log in with `admin` / `admin123`.

**API container keeps restarting** — check the logs:
```bash
docker logs oss-api
```
