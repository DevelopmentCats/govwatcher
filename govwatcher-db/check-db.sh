#!/bin/bash
# Simple script to check if the database is healthy and properly set up

# Allow container name to be passed as an argument, default to govwatcher-db-test
CONTAINER_NAME=${1:-govwatcher-db}

echo "GovWatcher Database Health Check"
echo "-------------------------------"
echo "Using container: $CONTAINER_NAME"

# Check if container is running
if [ "$(docker ps -q -f name=$CONTAINER_NAME)" ]; then
    echo "✅ Database container is running"
else
    echo "❌ Database container is not running"
    exit 1
fi

# Check PostgreSQL version
echo -n "PostgreSQL version: "
docker exec $CONTAINER_NAME psql -U postgres -c "SELECT version();" | grep PostgreSQL || echo "❌ Cannot get PostgreSQL version"

# Check if database exists
echo -n "Checking govwatcher database: "
DB_EXISTS=$(docker exec $CONTAINER_NAME psql -U postgres -lqt | cut -d \| -f 1 | grep -w govwatcher)
if [ -n "$DB_EXISTS" ]; then
    echo "✅ Database 'govwatcher' exists"
else
    echo "❌ Database 'govwatcher' does not exist"
    exit 1
fi

# Check users
echo "Checking database users..."
USERS=$(docker exec $CONTAINER_NAME psql -U postgres -c "SELECT COUNT(*) FROM pg_user WHERE usename IN ('api_user', 'archive_admin', 'readonly_user');" -t | xargs)
if [ "$USERS" -eq 3 ]; then
    echo "✅ All application users exist"
else
    echo "❌ Some application users are missing"
    echo "Current users:"
    docker exec $CONTAINER_NAME psql -U postgres -c "SELECT usename FROM pg_user WHERE usename IN ('api_user', 'archive_admin', 'readonly_user');" -t
fi

# Check tables
TABLES=("archives" "snapshots" "diffs" "social_posts" "archive_queue" "tags" "archive_tags" "users" "audit_log")
echo "Checking database tables..."
for TABLE in "${TABLES[@]}"; do
    TABLE_EXISTS=$(docker exec $CONTAINER_NAME psql -U postgres -d govwatcher -c "\dt $TABLE" | grep -w "$TABLE")
    if [ -n "$TABLE_EXISTS" ]; then
        echo "✅ Table '$TABLE' exists"
    else
        echo "❌ Table '$TABLE' does not exist"
    fi
done

# Check sample data
echo "Checking sample data..."
ARCHIVES_COUNT=$(docker exec $CONTAINER_NAME psql -U postgres -d govwatcher -c "SELECT COUNT(*) FROM archives;" -t | xargs)
echo "Archives count: $ARCHIVES_COUNT"
if [ "$ARCHIVES_COUNT" -gt 0 ]; then
    echo "✅ Sample data is loaded"
else
    echo "❌ No sample data found. You may need to run:"
    echo "   docker exec $CONTAINER_NAME psql -U postgres -d govwatcher -f /docker-entrypoint-initdb.d/02-sample-data.sql"
fi

echo "-------------------------------"
echo "Health check completed" 