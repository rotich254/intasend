#!/usr/bin/env bash
# Exit on error
set -o errexit

# Create directory for SQLite database on persistent disk if needed
mkdir -p db

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Run migrations - note we do this AFTER collecting static files
# because migrations depend on the static files being collected
python manage.py migrate 