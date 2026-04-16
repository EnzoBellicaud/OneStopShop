#!/bin/sh
set -e

python manage.py migrate
python manage.py seed_lookups

exec python manage.py run_scraper_worker
