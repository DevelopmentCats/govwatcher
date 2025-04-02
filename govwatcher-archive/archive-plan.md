# GovWatcher Archiving Plan

## Overview
This plan outlines the archiving component of GovWatcher, which will monitor and archive .gov websites and government social media accounts. The archiving system will detect and visualize changes over time, allowing users to view historical versions and diffs between versions.

## Data Sources
- Government websites (.gov domains) from:
  - https://raw.githubusercontent.com/cisagov/dotgov-data/main/current-full.csv
  - https://raw.githubusercontent.com/cisagov/dotgov-data/main/current-federal.csv
- Government social media accounts (Twitter/X, Facebook, Instagram, etc.)

## Archiving Solution: Hybrid Approach

Our GovWatcher archiving solution will use a hybrid approach, with ArchiveBox as the core archiving engine extended with custom components. This approach provides the best balance between leveraging existing tools and meeting our specific requirements.

### Core Component: ArchiveBox
[ArchiveBox](https://archivebox.io/) will serve as our primary archiving engine due to its:
- Purpose-built web archiving capabilities
- Multiple capture methods (screenshot, PDF, WARC)
- Open-source and self-hosted nature
- Existing API for automation
- Support for browser automation integration

### Custom Extensions
We'll extend ArchiveBox with custom components for:
1. **Diff Generation**: Custom tools built with htmldiff and image comparison libraries
2. **Social Media Monitoring**: Platform-specific tools like twarc for Twitter/X and F(b)arc for Facebook
3. **Scheduling and Prioritization**: Custom scheduling system for different monitoring frequencies
4. **Web Interface Integration**: Custom UI for displaying archives and changes
5. **WARC Management**: Tools for optimizing storage and retrieval of WARC files

## Technical Implementation

### Server Requirements (Resource-Optimized)
- Ubuntu Server (latest LTS)
- 4 CPU cores
- 12GB RAM
- Storage:
  - SSD: 100GB for OS and applications
  - Storage: Start with 1TB, expandable as archives grow
  - Database: 50GB partition

### Resource Optimization Strategies
- **Parallel Crawl Limiting**: Maximum 3-4 concurrent crawls
- **Memory Limits**: Docker container memory constraints (e.g., 2GB for ArchiveBox, 3GB for database)
- **Swap Configuration**: 4GB swap space to handle occasional spikes
- **Efficient Scheduling**: Time-distributed crawling to spread resource usage
- **Selective Archiving**: Prioritize text/HTML content over multimedia for less important sites
- **Browser Instance Management**: Up to 2 headless browser instances with queue system

### Software Components

#### Core Technologies
- Docker and Docker Compose for containerization (with resource constraints)
- PostgreSQL for metadata and change tracking (with optimized configuration)
- Redis for job queuing (lightweight configuration)
- ArchiveBox for webpage capture and storage
- PyWB for WARC replay (on-demand loading)
- Python for custom scripts and automation
- Node.js for processing and API layer
- Single headless browser instance (managed life cycle)

#### Installation Sequence
1. Base system setup (Ubuntu Server) with optimized defaults
2. Docker and Docker Compose with memory limits
3. Database setup (PostgreSQL with reduced cache settings)
4. ArchiveBox installation via Docker with resource constraints
5. PyWB setup for archive replay (configured for minimal footprint)
6. Custom components installation
7. Monitoring and resource usage alerting tools

### Archiving Process Flow

1. **Discovery**: Parse the .gov domain lists to create initial target list
2. **Prioritization**: Rank sites by importance, update frequency
3. **Initial Capture**: Gradual archival of sites in batches (not all at once)
4. **Scheduled Monitoring**: 
   - High priority: Weekly checks (staggered throughout the week)
   - Medium priority: Bi-weekly checks
   - Low priority: Monthly checks
   - Maximum 50-100 sites per day to manage resource usage
5. **Change Detection**:
   - Compare new captures with previous versions
   - Store diffs and highlight significant changes
   - Trigger alerts for major changes
6. **Storage Management**:
   - Compress archives immediately after creation
   - Implement aggressive retention policies
   - Incremental backup strategies

### Resource-Efficient Crawling Strategy
- Night-time scheduling for most intensive crawls
- Sequential processing for resource-heavy sites
- Parallel crawling for up to 4 lightweight sites simultaneously
- Dynamic scheduling based on server load
- Automatic pausing when resource thresholds are approached

### Social Media Monitoring
- Use platform APIs where available (Twitter/X, Facebook, etc.)
- Implement API rate limit handling
- Archive posts, replies, and media content
- Track engagement metrics
- Tools to implement:
  - twarc for Twitter/X (configured for minimal memory footprint)
  - F(b)arc for Facebook (with request throttling)
  - Social Feed Manager for multiple platforms (with reduced concurrency)

### Diff Generation System
- HTML comparison using tools like `htmldiff` or custom solution
- Text-focused diff generation prioritized over visual diffs
- Selective screenshot comparison for high-priority sites only
- Metadata tracking (headers, links, etc.)
- Components to implement:
  - warcdb for indexing content (with reduced indexing scope)
  - OutbackCDX for capture indexing (with optimized settings)
  - Custom diffing tools integrated with the database

#### Diff Tools and Approaches
1. **HTML Diffing**:
   - Google's diff_match_patch library for robust text diffing
   - Code normalization before comparison (for smaller memory footprint)
   - BeautifulSoup for HTML parsing and structure normalization

2. **Visual Comparison** (selective usage):
   - Lightweight screenshot comparison for high-priority sites only
   - Optional full visual diffing based on resource availability

3. **Custom Diff UI**:
   - Side-by-side comparison view
   - Inline changes with color coding
   - On-demand loading of diff content

4. **Diff Metadata**:
   - Track types of changes (content, structure, style, functionality)
   - Categorize changes by significance
   - Link changes to specific site sections

5. **Storage and Indexing**:
   - Store diff results in structured database
   - Selective indexing based on importance
   - Implement efficient data pruning strategies

## File Formats and Storage

### Primary Format: WARC
- Web ARChive (WARC) format is the ISO standard (ISO 28500) for web archives
- Contains full HTTP requests and responses
- Preserves metadata and context
- Compatible with various replay and analysis tools

### Secondary Formats
- Text extraction for primary storage
- Selective screenshots for high-priority content
- PDF generation on demand rather than by default
- HTML snapshots for quick access

### Storage Strategy
- Aggressive compression for all archives
- Deduplication at file and content levels
- Tiered storage approach:
  - Hot storage: Recent archives, frequently accessed (100GB)
  - Warm storage: Older archives, occasionally accessed (400GB)
  - Cold storage: Historical archives, rarely accessed (remaining space)

## Scalability Plan
- Start with top 50 .gov sites to validate approach
- Add sites gradually while monitoring resource usage
- Implement adaptive crawl scheduling based on system load
- Consider additional storage before additional RAM/CPU
- Scale horizontally (additional small servers) rather than vertically if needed

## Monitoring & Maintenance
- Resource usage monitoring with alerts at 75% thresholds
- Crawler performance metrics
- Failed archive attempts tracking
- Regular database optimization
- Log rotation and aggressive pruning

## Security Considerations
- Run components with principle of least privilege
- Regular security updates
- Implement rate limiting for public interfaces
- Consider Tor/proxy usage for crawling
- Sanitize archived content for viewing

## Implementation Challenges and Risk Mitigation

### Technical Challenges

1. **Resource Constraints**
   - **Challenge**: Operating within 8GB RAM limit with multiple components
   - **Mitigation**: Aggressive scheduling, component isolation, swap configuration, and runtime prioritization

2. **Crawling Complex Sites**
   - **Challenge**: Modern .gov sites use JavaScript, AJAX, and dynamic content
   - **Mitigation**: Targeted rendering for important content, text-first approach for most sites

3. **Storage Growth**
   - **Challenge**: Archive size can grow exponentially with frequent crawls
   - **Mitigation**: Aggressive deduplication, content-based hashing, and selective archiving

4. **Diverse Content Types**
   - **Challenge**: Sites contain PDFs, video, interactive elements 
   - **Mitigation**: Prioritize text content, selectively archive multimedia

### Operational Challenges

1. **Resource Allocation**
   - **Challenge**: Balancing limited resources across crawling tasks
   - **Mitigation**: Time-distributed scheduling, priority-based queuing, background processing

2. **False Positives in Change Detection**
   - **Challenge**: Cosmetic or irrelevant changes triggering alerts
   - **Mitigation**: Focus on semantic content changes over presentation changes

3. **Monitoring at Scale**
   - **Challenge**: Managing thousands of website monitors with limited resources
   - **Mitigation**: Batch processing, incremental monitoring, adaptive schedules

## Development Roadmap
1. Proof of concept with core archiving system (2 weeks)
   - Set up basic ArchiveBox instance with resource constraints
   - Test with sample .gov websites (10-20 sites)
   - Establish efficient storage architecture
2. Basic diff generation and UI (2 weeks)
   - Implement lightweight HTML diffing
   - Create simple UI for viewing changes
   - Set up database for tracking versions with optimized indexes
3. Social media monitoring integration (1 week)
   - Implement selective Twitter/X archiving
   - Add Facebook page monitoring for high-priority accounts
   - Create unified view of social content
4. Scaling improvements and optimization (ongoing)
   - Resource usage optimization
   - Storage efficiency improvements
   - Crawl scheduling optimization
5. Advanced features (as resources allow)
   - Selective full-text search
   - Basic analytics
   - Limited API access 

### Database Schema

The PostgreSQL database will store metadata about archives, snapshots, and diffs with the following schema:

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
```

### Content Serving Mechanism

The archiving system will store content in a structured format that can be directly accessed by the backend API:

1. **Organized Storage Structure**:
   ```
   /data/archives/
   ├── <domain-id>/
   │   ├── snapshots/
   │   │   ├── <snapshot-id>/
   │   │   │   ├── original.warc  # Original WARC file
   │   │   │   ├── screenshot.png # Full page screenshot
   │   │   │   ├── content.html   # Extracted HTML
   │   │   │   ├── content.txt    # Extracted text
   │   │   │   └── content.pdf    # PDF version
   │   │
   │   └── diffs/
   │       ├── <old-id>_<new-id>/
   │       │   ├── diff.json      # Structured diff data
   │       │   └── visual-diff.png # Visual diff image
   ```

2. **Direct Volume Access**:
   - The archive data volume is mounted read-only to the API container
   - API serves content directly from the filesystem
   - Database records point to relative paths within this structure
   - This approach eliminates the need for a separate content server

3. **Content Format Standards**:
   - WARC files follow ISO 28500 standard
   - Diffs stored in a format compatible with frontend visualization needs
   - Metadata stored in both database and accompanying JSON files
   - All timestamps use ISO 8601 format for consistency

## Integration with Backend API

To support the backend API's needs, the archiving system will:

1. **Provide Database Access**:
   - Create a read-only database user specifically for the backend API
   - Apply proper indexing to support API query patterns
   - Document table relationships and query patterns

2. **Shared Volume Access**:
   - Store all archive files in a predictable, structured format
   - Provide a shared Docker volume that the backend can mount read-only
   - Ensure file permissions allow read access from the backend container
   - Maintain a consistent directory structure and naming convention

3. **Event Notifications**:
   - Implement a simple webhook system to notify backend of significant events:
     - New snapshot completed
     - Diff generated
     - Major change detected
   - This allows the backend to invalidate caches and update real-time data

4. **Standardized Formats**:
   - Generate diffs in a format compatible with react-diff-view
   - Structure metadata consistently for frontend consumption
   - Use standardized timestamps (ISO 8601) across all components

### System Initialization Process

The archiving system includes an initialization process to bootstrap monitoring:

1. **Initial Setup Script**:
   ```bash
   # Initialize the system with .gov domains
   python setup.py --source-csv=current-full.csv --priority-csv=current-federal.csv
   ```

2. **Domain Import Process**:
   - Parse CSV files from CISA
   - Create records in `archives` table
   - Assign initial priorities (federal domains get higher priority)
   - Schedule initial captures in the queue

3. **Configuration Process**:
   - Generate default configuration files
   - Set up directory structure for storage
   - Initialize database with schema
   - Create necessary Docker volumes

4. **First-Run Workflow**:
   - Capture high-priority sites first
   - Build initial index
   - Generate system health report

## Integration with Backend API

To support the backend API's needs, the archiving system will:

1. **Provide Database Access**:
   - Create a read-only database user specifically for the backend API
   - Apply proper indexing to support API query patterns
   - Document table relationships and query patterns

2. **Shared Volume Access**:
   - Store all archive files in a predictable, structured format
   - Provide a shared Docker volume that the backend can mount read-only
   - Ensure file permissions allow read access from the backend container
   - Maintain a consistent directory structure and naming convention

3. **Event Notifications**:
   - Implement a simple webhook system to notify backend of significant events:
     - New snapshot completed
     - Diff generated
     - Major change detected
   - This allows the backend to invalidate caches and update real-time data

4. **Standardized Formats**:
   - Generate diffs in a format compatible with react-diff-view
   - Structure metadata consistently for frontend consumption
   - Use standardized timestamps (ISO 8601) across all components

### System Initialization Process

The archiving system includes an initialization process to bootstrap monitoring:

1. **Initial Setup Script**:
   ```bash
   # Initialize the system with .gov domains
   python setup.py --source-csv=current-full.csv --priority-csv=current-federal.csv
   ```

2. **Domain Import Process**:
   - Parse CSV files from CISA
   - Create records in `archives` table
   - Assign initial priorities (federal domains get higher priority)
   - Schedule initial captures in the queue

3. **Configuration Process**:
   - Generate default configuration files
   - Set up directory structure for storage
   - Initialize database with schema
   - Create necessary Docker volumes

4. **First-Run Workflow**:
   - Capture high-priority sites first
   - Build initial index
   - Generate system health report 