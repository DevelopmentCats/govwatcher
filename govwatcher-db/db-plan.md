# GovWatcher Database Plan

## Overview
This plan outlines the PostgreSQL database implementation for GovWatcher, which serves as the central metadata store for the archiving system. The database will store information about monitored websites, snapshots, diffs, and related social media content, while optimizing for both read and write operations.

## Design Goals
- **Reliability**: Ensure data integrity and durability
- **Performance**: Optimize for both read-heavy (API) and write-heavy (Archiving) operations
- **Scalability**: Support growing archive volume without degradation
- **Security**: Implement proper access controls for different system components
- **Maintainability**: Follow database best practices for long-term management

## Technical Implementation

### Database Version & Configuration
- **PostgreSQL Version**: 14 or 15 (LTS)
- **Character Set**: UTF-8
- **Collation**: en_US.UTF-8
- **Transaction Isolation Level**: READ COMMITTED (default)

### Resource Requirements
- **CPU**: 2-4 dedicated cores
- **RAM**: 8GB minimum (4GB for PostgreSQL, buffer cache)
- **Storage**: 
  - 50GB for database files (initial)
  - Growth estimate: ~5GB per 10,000 archive entries
  - Separate volume/partition from OS
  - SSD strongly recommended

### Schema Design

The database schema will include these core tables:

```sql
-- Information about monitored websites
CREATE TABLE archives (
    id SERIAL PRIMARY KEY,
    domain VARCHAR(255) NOT NULL,
    domain_type VARCHAR(50),
    agency VARCHAR(255),
    organization_name VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(50),
    security_contact_email VARCHAR(255),
    priority INTEGER DEFAULT 3, -- 1=high, 2=medium, 3=low
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_checked_at TIMESTAMP,
    last_changed_at TIMESTAMP,
    enabled BOOLEAN DEFAULT TRUE,
    UNIQUE(domain)
);

-- Individual website captures
CREATE TABLE snapshots (
    id SERIAL PRIMARY KEY,
    archive_id INTEGER REFERENCES archives(id),
    capture_timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    warc_path VARCHAR(512) NOT NULL,
    screenshot_path VARCHAR(512),
    html_path VARCHAR(512),
    text_path VARCHAR(512),
    pdf_path VARCHAR(512),
    content_hash VARCHAR(128),
    status INTEGER, -- HTTP status code
    size_bytes BIGINT,
    error_message TEXT,
    metadata JSONB,
    UNIQUE(archive_id, capture_timestamp)
);

-- Stored differences between snapshots
CREATE TABLE diffs (
    id SERIAL PRIMARY KEY,
    archive_id INTEGER REFERENCES archives(id),
    old_snapshot_id INTEGER REFERENCES snapshots(id),
    new_snapshot_id INTEGER REFERENCES snapshots(id),
    diff_timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    diff_path VARCHAR(512),
    stats JSONB, -- Contains statistics like num_changes, etc.
    significance INTEGER, -- 1=minor, 2=moderate, 3=major
    UNIQUE(old_snapshot_id, new_snapshot_id)
);

-- Related social media content
CREATE TABLE social_posts (
    id SERIAL PRIMARY KEY,
    archive_id INTEGER REFERENCES archives(id),
    platform VARCHAR(50) NOT NULL, -- twitter, facebook, etc.
    post_id VARCHAR(255) NOT NULL,
    post_url VARCHAR(512) NOT NULL,
    post_text TEXT,
    author VARCHAR(255),
    posted_at TIMESTAMP,
    collected_at TIMESTAMP NOT NULL DEFAULT NOW(),
    engagement_stats JSONB, -- likes, shares, etc.
    UNIQUE(platform, post_id)
);

-- Archive processing queue
CREATE TABLE archive_queue (
    id SERIAL PRIMARY KEY,
    archive_id INTEGER REFERENCES archives(id),
    operation VARCHAR(50) NOT NULL, -- initial_capture, update_check, etc.
    status VARCHAR(20) DEFAULT 'pending', -- pending, in_progress, completed, failed
    priority INTEGER DEFAULT 5,
    scheduled_for TIMESTAMP NOT NULL,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    retries INTEGER DEFAULT 0,
    UNIQUE(archive_id, operation, status) WHERE status IN ('pending', 'in_progress')
);

-- Tags for categorizing archives
CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    UNIQUE(name)
);

-- Relation table for archive tags
CREATE TABLE archive_tags (
    archive_id INTEGER REFERENCES archives(id),
    tag_id INTEGER REFERENCES tags(id),
    PRIMARY KEY (archive_id, tag_id)
);

-- System users for access control
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    password_hash VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    role VARCHAR(20) NOT NULL, -- admin, operator, viewer
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_login TIMESTAMP,
    enabled BOOLEAN DEFAULT TRUE,
    UNIQUE(username)
);

-- Audit logging for important operations
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL, -- archive, snapshot, etc.
    entity_id INTEGER,
    details JSONB,
    ip_address VARCHAR(45),
    timestamp TIMESTAMP NOT NULL DEFAULT NOW()
);
```

### Required Indexes

To optimize query performance, the following indexes will be created:

```sql
-- Archives table indexes
CREATE INDEX idx_archives_domain ON archives(domain);
CREATE INDEX idx_archives_priority ON archives(priority);
CREATE INDEX idx_archives_last_changed ON archives(last_changed_at DESC NULLS LAST);

-- Snapshots table indexes
CREATE INDEX idx_snapshots_archive_id ON snapshots(archive_id);
CREATE INDEX idx_snapshots_capture_time ON snapshots(capture_timestamp DESC);
CREATE INDEX idx_snapshots_content_hash ON snapshots(content_hash);

-- Diffs table indexes
CREATE INDEX idx_diffs_archive_id ON diffs(archive_id);
CREATE INDEX idx_diffs_significance ON diffs(significance);
CREATE INDEX idx_diffs_timestamp ON diffs(diff_timestamp DESC);
CREATE INDEX idx_diffs_new_snapshot ON diffs(new_snapshot_id);
CREATE INDEX idx_diffs_old_snapshot ON diffs(old_snapshot_id);

-- Social posts indexes
CREATE INDEX idx_social_posts_archive ON social_posts(archive_id);
CREATE INDEX idx_social_posts_platform ON social_posts(platform, post_id);
CREATE INDEX idx_social_posts_posted_at ON social_posts(posted_at DESC);

-- Queue indexes
CREATE INDEX idx_queue_status ON archive_queue(status);
CREATE INDEX idx_queue_scheduled ON archive_queue(scheduled_for ASC);
CREATE INDEX idx_queue_priority ON archive_queue(priority ASC);
```

### JSONB Indexes
For the JSONB fields, we'll use GIN indexes to optimize queries:

```sql
-- Index for JSONB metadata
CREATE INDEX idx_snapshots_metadata ON snapshots USING GIN (metadata);
CREATE INDEX idx_diffs_stats ON diffs USING GIN (stats);
CREATE INDEX idx_social_engagement ON social_posts USING GIN (engagement_stats);
```

## Database User Roles and Access Control

The database will implement a role-based access control system to ensure proper data security:

```sql
-- Create role groups
CREATE ROLE govwatcher_admin;
CREATE ROLE govwatcher_api;
CREATE ROLE govwatcher_archive;
CREATE ROLE govwatcher_readonly;

-- Create application users
CREATE USER archive_admin WITH PASSWORD 'secure_password1';
CREATE USER api_user WITH PASSWORD 'secure_password2';
CREATE USER readonly_user WITH PASSWORD 'secure_password3';

-- Grant role memberships
GRANT govwatcher_admin TO archive_admin;
GRANT govwatcher_api TO api_user;
GRANT govwatcher_readonly TO readonly_user;

-- Set up permissions
GRANT ALL ON ALL TABLES IN SCHEMA public TO govwatcher_admin;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO govwatcher_api;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO govwatcher_readonly;

-- Specific permissions for queue management
GRANT ALL ON TABLE archive_queue TO govwatcher_archive;
```

## Performance Optimization

### Connection Pooling
- Use PgBouncer for connection pooling
- Configure pool size based on component needs:
  - Archive System: 5-10 connections
  - API: 20-30 connections
- Set statement timeout to prevent long-running queries

### Memory Configuration
- `shared_buffers`: 25% of available RAM (2GB for 8GB server)
- `work_mem`: 64MB (adjusted based on query complexity)
- `maintenance_work_mem`: 256MB for vacuum operations
- `effective_cache_size`: 4GB (50% of system memory)
- `wal_buffers`: 16MB
- `max_connections`: 100

### Query Optimization
- Regular EXPLAIN ANALYZE for common queries
- Create materialized views for complex analytics queries
- Implement partitioning for large tables (e.g., snapshots by month)
- Create summary tables for dashboard statistics

## Backup and Recovery Strategy

### Continuous Archiving with WAL
- Enable WAL archiving for point-in-time recovery
- Configure `wal_level = replica`
- Store WAL archives in a separate storage location

### Backup Schedule
- Daily full backup (pgBackRest or pg_dump)
- Hourly WAL archiving
- Retention policy:
  - Daily backups: 7 days
  - Weekly backups: 4 weeks
  - Monthly backups: 12 months

### Recovery Testing
- Monthly recovery tests from backup
- Document recovery time objectives (RTO)
- Validate data integrity after recovery

## High Availability Configuration (Future)

For future scalability, consider implementing:

- Primary-Standby replication
- Connection pooling with PgBouncer
- Read replicas for API queries
- Integration with monitoring system (Prometheus/Grafana)

## Docker Configuration

```dockerfile
FROM postgres:14

# Copy custom configuration
COPY postgresql.conf /etc/postgresql/postgresql.conf
COPY pg_hba.conf /etc/postgresql/pg_hba.conf

# Initialize extensions and roles
COPY init-scripts/ /docker-entrypoint-initdb.d/

# Environment variables set in docker-compose.yml
ENV POSTGRES_PASSWORD=secure_password
ENV POSTGRES_USER=postgres
ENV POSTGRES_DB=govwatcher

# Expose PostgreSQL port
EXPOSE 5432

# Set command to use custom config
CMD ["postgres", "-c", "config_file=/etc/postgresql/postgresql.conf"]
```

## Initial Database Setup

The initialization scripts will:

1. Create the database schema
2. Create application roles
3. Set up indexes
4. Create required extensions:
   - `pgcrypto` for password hashing
   - `btree_gin` for GIN index support
   - `pg_stat_statements` for query analysis

## Monitoring and Maintenance

### Regular Maintenance Tasks
- VACUUM ANALYZE: Weekly
- Index rebuilding: Monthly
- Statistics collection: Daily
- Database size monitoring

### Health Checks
- Connection count monitoring
- Query performance monitoring
- Disk space usage alerts
- Lock monitoring
- Long-running query detection

## Integration with Other Components

### Archive System Access
- Direct write access for storing new snapshots and diffs
- Batch operations for efficiency
- Transaction management for consistency

### API Access
- Read-only access for most operations
- Limited write access for specific endpoints
- Connection pooling to manage load

### Redis Integration
- Store transient query results in Redis instead of temporary tables
- Cache frequent queries (e.g., recent changes list)
- Use Redis for queue status instead of frequent DB polling

## Development Workflow

### Local Development Setup
- Docker Compose configuration
- Sample data generation scripts
- Schema migration tools

### Migration Strategy
- Use Flyway or Sqitch for schema versioning
- Backward compatible changes when possible
- Testing migrations in staging environment

## Security Considerations

### Data Protection
- Encrypt sensitive fields
- Regular security audits
- Minimal privileges for service accounts

### Access Control
- Network level restrictions (firewall)
- Strong password policies
- Regular permission review

### Auditing
- Query logging for sensitive operations
- Login attempt monitoring
- Change tracking for critical data

## Future Enhancements

1. **Database Partitioning**
   - Implement table partitioning for snapshots and social_posts
   - Partition by time periods (monthly)

2. **Read Replicas**
   - Add read replicas for API access
   - Implement connection routing based on query type

3. **Full-Text Search**
   - Integrate PostgreSQL full-text search for content
   - Create search indexes for archived content

4. **Advanced Analytics**
   - Implement analytics-specific schemas
   - Create materialized views for dashboard metrics

5. **Data Retention Policies**
   - Automated archiving of old, less accessed data
   - Selective pruning of historical data 