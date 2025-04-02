# GovWatcher Database Component

This directory contains the PostgreSQL database configuration and initialization scripts for the GovWatcher platform.

## Overview

The GovWatcher database stores metadata for the archiving system, including:
- Information about monitored websites
- Snapshots of website captures
- Differences between snapshots
- Social media content
- Processing queue

## Quick Start

### Using Docker Compose

The simplest way to run the database is using Docker Compose from the root project directory:

```bash
# Start all GovWatcher services
docker compose up -d

# Or start just the database
docker compose up -d db
```

### Standalone Database Setup

You can also run the database container by itself:

```bash
cd govwatcher-db

# Create a .env file from the example (if you haven't already)
cp .env.example .env

# Edit the .env file with your preferred settings
nano .env

# Build and run the container with environment variables from .env
docker-compose -f docker-compose.db-only.yml up -d
```

To ensure your .env file is being read correctly, you can verify with:

```bash
# List the container with environment variables
docker inspect govwatcher-db | grep -A 20 "Env"
```

## Database Schema

The database schema is defined in `init-scripts/01-init-schema.sql` and includes:

- `archives`: Monitored websites
- `snapshots`: Website captures
- `diffs`: Differences between snapshots
- `social_posts`: Related social media content
- `archive_queue`: Processing queue
- `tags` and `archive_tags`: Categorization
- `users`: System users
- `audit_log`: System audit trail

## Database Users

The database has three main application users:

1. `archive_admin`: Full access for the archive component
2. `api_user`: Read access with limited write capabilities for the API
3. `readonly_user`: Read-only access for reporting

## Sample Data

For development and testing, sample data is available in `init-scripts/02-sample-data.sql`.

To load the sample data manually:

```bash
docker exec -it govwatcher-db psql -U postgres -d govwatcher -f /docker-entrypoint-initdb.d/02-sample-data.sql
```

## Configuration

The database configuration is in `postgresql.conf` and includes:

- Memory settings optimized for performance
- Autovacuum configured for regular maintenance
- Logging for debugging and monitoring
- WAL (Write-Ahead Log) settings for durability

## Maintenance

### Backup and Restore

To backup the database:

```bash
docker exec -it govwatcher-db pg_dump -U postgres -d govwatcher -F c -f /tmp/govwatcher-backup.dump
docker cp govwatcher-db:/tmp/govwatcher-backup.dump ./backups/
```

To restore from backup:

```bash
docker cp ./backups/govwatcher-backup.dump govwatcher-db:/tmp/
docker exec -it govwatcher-db pg_restore -U postgres -d govwatcher -c /tmp/govwatcher-backup.dump
```

### Database Monitoring

Check database status:

```bash
docker exec -it govwatcher-db psql -U postgres -c "SELECT version();"
docker exec -it govwatcher-db psql -U postgres -c "SELECT count(*) FROM archives;"
```

Monitor connections:

```bash
docker exec -it govwatcher-db psql -U postgres -c "SELECT * FROM pg_stat_activity;"
```

### Connection Information

- Host: localhost (or container name in Docker network)
- Port: 5432
- Database: govwatcher
- Superuser: postgres (password in .env)
- Application users: archive_admin, api_user, readonly_user 

## Health Check

The `check-db.sh` script provides a quick health check for your database container:

```bash
# Run health check (defaults to checking the container named govwatcher-db)
./check-db.sh

# Or specify a custom container name
./check-db.sh your-container-name
```

This script verifies:
- If the database container is running
- PostgreSQL version
- Database existence
- Required users
- Required tables
- Sample data

### Troubleshooting Container Names

By default, the following container names are used:
- `govwatcher-db` - When using either the main project's docker-compose.yml or this directory's docker-compose.db-only.yml
- `govwatcher-db-test` - Used by previous versions of docker-compose.db-only.yml

If your container has a different name, either:
1. Pass the container name to the script: `./check-db.sh your-container-name`
2. Stop and remove existing containers, then restart using the docker-compose file 