#!/usr/bin/env bash
# Exit on error
set -o errexit

# Create directory for SQLite database on persistent disk if needed
mkdir -p db 2>/dev/null || true

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Run migrations - note we do this AFTER collecting static files
# because migrations depend on the static files being collected
python manage.py migrate 