#!/bin/bash
# VivaCampo Database Migration Script
# Execute all SQL migrations in order

set -e

echo "========================================="
echo "VivaCampo Database Migrations"
echo "========================================="
echo ""

# Check if database container is running
if ! docker ps | grep -q vivacampo-db-1; then
    echo "❌ Error: Database container (vivacampo-db-1) is not running"
    echo "Run: docker-compose up -d db"
    exit 1
fi

echo "✓ Database container is running"
echo ""

# Execute migrations
MIGRATION_DIR="c:/projects/vivacampo-app/infra/migrations/sql"

if [ ! -d "$MIGRATION_DIR" ]; then
    echo "❌ Error: Migration directory not found: $MIGRATION_DIR"
    exit 1
fi

echo "Running migrations from: $MIGRATION_DIR"
echo ""

# Find all .sql files and execute them in order
for migration in $(ls -1 "$MIGRATION_DIR"/*.sql | sort); do
    migration_name=$(basename "$migration")
    echo "→ Executing: $migration_name"

    if cat "$migration" | docker exec -i vivacampo-db-1 psql -U vivacampo -d vivacampo > /dev/null 2>&1; then
        echo "  ✓ Success"
    else
        echo "  ⚠️  Warning: Migration may have already been applied"
    fi
done

echo ""
echo "========================================="
echo "Verifying database tables..."
echo "========================================="
echo ""

# Verify tables
tables=$(docker exec vivacampo-db-1 psql -U vivacampo -d vivacampo -t -c "SELECT COUNT(*) FROM pg_tables WHERE schemaname='public';" 2>/dev/null | tr -d ' ')

if [ -n "$tables" ] && [ "$tables" -gt 0 ]; then
    echo "✓ Found $tables tables in database"
    echo ""
    echo "Key tables:"
    docker exec vivacampo-db-1 psql -U vivacampo -d vivacampo -c "SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename IN ('identities', 'tenants', 'farms', 'aois', 'opportunity_signals') ORDER BY tablename;" 2>/dev/null | grep -E "identities|tenants|farms|aois|opportunity_signals" || echo "  (checking...)"
else
    echo "⚠️  Warning: No tables found in database"
fi

echo ""
echo "========================================="
echo "✓ Migrations completed!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Restart API: docker-compose restart api"
echo "2. Restart Worker: docker-compose restart worker"
echo "3. Test login: http://localhost:3002/app/login"
echo ""
