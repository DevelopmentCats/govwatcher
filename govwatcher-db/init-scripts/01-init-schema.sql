-- GovWatcher Database Initialization Script

-- Create application users with passwords from environment variables
CREATE USER api_user WITH PASSWORD '${API_PASSWORD}';
CREATE USER archive_admin WITH PASSWORD '${ARCHIVE_PASSWORD}';
CREATE USER readonly_user WITH PASSWORD '${READONLY_PASSWORD}';

-- Create roles
CREATE ROLE govwatcher_admin;
CREATE ROLE govwatcher_api;
CREATE ROLE govwatcher_readonly;

-- Grant role memberships
GRANT govwatcher_admin TO archive_admin;
GRANT govwatcher_api TO api_user;
GRANT govwatcher_readonly TO readonly_user;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS btree_gin;

-- Create schema
CREATE SCHEMA IF NOT EXISTS public;

-- Archive table for monitored websites
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

-- Snapshots table for website captures
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

-- Diffs table for storing differences between snapshots
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

-- Social media posts related to archives
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
    retries INTEGER DEFAULT 0
);

CREATE UNIQUE INDEX unique_pending_jobs ON archive_queue (archive_id, operation, status)
    WHERE status IN ('pending', 'in_progress');

-- Tags for categorizing archives
CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    UNIQUE(name)
);

-- Archive tags relation table
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

-- Create necessary indexes
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

-- JSONB indexes
CREATE INDEX idx_snapshots_metadata ON snapshots USING GIN (metadata);
CREATE INDEX idx_diffs_stats ON diffs USING GIN (stats);
CREATE INDEX idx_social_engagement ON social_posts USING GIN (engagement_stats);

-- Set up permissions
GRANT ALL ON ALL TABLES IN SCHEMA public TO govwatcher_admin;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO govwatcher_api;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO govwatcher_readonly;

-- Grant sequence permissions
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO govwatcher_admin;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO govwatcher_api;

-- Create initial admin user (password: admin)
INSERT INTO users (username, password_hash, email, role) 
VALUES ('admin', crypt('admin', gen_salt('bf')), 'admin@example.com', 'admin'); 