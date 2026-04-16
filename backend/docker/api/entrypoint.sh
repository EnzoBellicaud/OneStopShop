#!/bin/sh
set -e

python manage.py migrate
python manage.py seed_lookups
python manage.py seed_offers

exec python manage.py runserver 0.0.0.0:8000
