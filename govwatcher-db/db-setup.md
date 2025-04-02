# GovWatcher Archive Database Setup

This document provides instructions for setting up and testing the database component of the GovWatcher Archive system.

## Database Schema

The GovWatcher Archive system uses a PostgreSQL database with the following tables:

- `archives`: Information about monitored websites
- `snapshots`: Individual website captures
- `diffs`: Stored differences between snapshots
- `social_posts`: Related social media content
- `archive_queue`: Processing queue for archive operations
- Additional support tables: `tags`, `archive_tags`, `users`, `audit_log`

## Docker Setup

The easiest way to set up the database for development and testing is using Docker Compose.

### Testing the Database and Archive Together

1. Navigate to the govwatcher-archive directory:
   ```bash
   cd govwatcher-archive
   ```

2. Start the test containers using Docker Compose:
   ```bash
   docker-compose -f docker-compose.test.yml up -d
   ```

3. Verify that the containers are running:
   ```bash
   docker-compose -f docker-compose.test.yml ps
   ```

4. To view the logs:
   ```bash
   docker-compose -f docker-compose.test.yml logs -f
   ```

5. To stop the containers:
   ```bash
   docker-compose -f docker-compose.test.yml down
   ```

## Connecting to the Database

You can connect to the database using the psql command line tool:

```bash
docker exec -it govwatcher-db-test psql -U postgres -d govwatcher
```

### Connection Information

- Host: localhost
- Port: 5432
- Database: govwatcher
- Users:
  - postgres (superuser): password is 'devpassword'
  - archive_admin: password is 'archive_password'
  - api_user: password is 'api_password'
  - readonly_user: password is 'readonly_password'

## Importing Sample Data

To import sample data for testing:

1. Connect to the database container:
   ```bash
   docker exec -it govwatcher-db-test bash
   ```

2. Navigate to the mounted volume with sample data:
   ```bash
   cd /docker-entrypoint-initdb.d/
   ```

3. Run any additional import scripts:
   ```bash
   psql -U postgres -d govwatcher -f 02-sample-data.sql
   ```

## Manual Database Initialization

If you need to manually create the schema:

1. Connect to the database container:
   ```bash
   docker exec -it govwatcher-db-test bash
   ```

2. Run the initialization script:
   ```bash
   cd /docker-entrypoint-initdb.d/
   psql -U postgres -d govwatcher -f 01-init-schema.sql
   ```

## Testing with the Archive Component

After setting up the database, you can test the archive component:

1. Make sure all containers are running:
   ```bash
   docker-compose -f docker-compose.test.yml ps
   ```

2. Import some sample domains:
   ```bash
   docker exec -it govwatcher-archive-test python src/main.py import --file /path/to/domains.csv
   ```

3. Trigger a manual crawl for testing:
   ```bash
   docker exec -it govwatcher-archive-test python src/main.py crawl --domain example.gov
   ```

4. Run the archive server in debug mode:
   ```bash
   docker exec -it govwatcher-archive-test python src/main.py server --debug
   ``` 