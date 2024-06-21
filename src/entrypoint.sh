#!/bin/sh

# Run Alembic migrations
alembic upgrade head

# Start the application
poetry run uwsgi --ini uwsgi.ini