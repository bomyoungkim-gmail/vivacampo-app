#!/bin/bash
# Database initialization script
# Runs automatically when database container starts

set -e

echo "[db-init] Waiting for PostgreSQL to be ready..."
until pg_isready -U vivacampo -d vivacampo; do
  sleep 1
done

echo "[db-init] PostgreSQL is ready"
echo "[db-init] Checking if migrations needed..."

# Check if identities table exists
if psql -U vivacampo -d vivacampo -tAc "SELECT 1 FROM pg_tables WHERE schemaname='public' AND tablename='identities';" | grep -q 1; then
    echo "[db-init] Database already initialized (identities table exists)"
else
    echo "[db-init] Running migrations..."

    # Run migration 001
    if [ -f /docker-entrypoint-initdb.d/001_initial_schema.sql ]; then
        echo "[db-init] Applying 001_initial_schema.sql..."
        psql -U vivacampo -d vivacampo -f /docker-entrypoint-initdb.d/001_initial_schema.sql
    fi

    # Run migration 002
    if [ -f /docker-entrypoint-initdb.d/002_rename_copilot_to_ai_assistant.sql ]; then
        echo "[db-init] Applying 002_rename_copilot_to_ai_assistant.sql..."
        psql -U vivacampo -d vivacampo -f /docker-entrypoint-initdb.d/002_rename_copilot_to_ai_assistant.sql
    fi

    echo "[db-init] Migrations completed!"
fi

echo "[db-init] Database initialization complete"
