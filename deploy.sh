#!/bin/bash
set -e

echo "Deploying ClearFeed..."

cd /home/clearfeed/ClearFeed

echo "Pulling latest code..."
git pull

echo "Syncing dependencies..."
uv sync

echo "Running migrations..."
uv run python backend/manage.py migrate --noinput

echo "Collecting static files..."
uv run python backend/manage.py collectstatic --noinput

echo "Restarting Django..."
systemctl --user restart clearfeed-django.service

echo "Restarting qcluster..."
systemctl --user restart clearfeed-qcluster.service

echo "Deploy complete!"