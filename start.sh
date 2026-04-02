#!/bin/bash

# Exit on error
set -e

echo "Starting Akompta Backend Setup..."

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start Gunicorn
echo "Starting Gunicorn..."
exec gunicorn --bind 0.0.0.0:7860 --workers 3 --timeout 120 Akompta.wsgi:application
