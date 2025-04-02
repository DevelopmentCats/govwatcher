# GovWatcher Backend API Plan

## Overview
This plan outlines the API backend component for GovWatcher, which will serve as the intermediary between the frontend application and the archiving system. The backend API will provide structured access to archived data, diff information, and system status while enforcing access controls and optimizing data delivery.

## Design Goals
- **Lightweight**: Minimal resource footprint
- **Fast**: Optimized for quick response times
- **Scalable**: Ability to handle increased load independently from archiving system
- **Clear Interfaces**: Well-defined API contracts for both frontend and archiving system
- **Resilient**: Tolerant of archiving system maintenance or downtime

## Architecture

### Technology Stack
- **Framework**: Express.js (Node.js) or FastAPI (Python)
- **Database Access**: Direct access to the archiving system's PostgreSQL database (read-only operations)
- **Caching**: Redis for response caching and performance optimization
- **API Documentation**: OpenAPI/Swagger for automatic documentation

### Component Relationships
```
+-------------+       +--------------+       +------------------+
|             |       |              |       |                  |
|  Frontend   | <---> |  Backend API | <---> |  Archiving System|
|             |       |              |       |                  |
+-------------+       +--------------+       +------------------+
                             |
                             v
                      +--------------+
                      |              |
                      |  PostgreSQL  |
                      |  Database    |
                      |              |
                      +--------------+
```

## API Endpoints

### Archive Management
- `GET /api/archives` - List all archived websites with filtering options
- `GET /api/archives/:id` - Get metadata for a specific archived website
- `GET /api/archives/:id/snapshots` - List all snapshots for a specific website
- `GET /api/archives/:id/snapshots/:snapshotId` - Get specific snapshot details
- `GET /api/archives/:id/snapshots/:snapshotId/content` - Get snapshot content (proxy to archive)

### Diff Operations
- `GET /api/diffs/:archiveId` - List all diffs for a website
- `GET /api/diffs/:archiveId/:snapshotId1/:snapshotId2` - Get diff between two snapshots
- `GET /api/diffs/:archiveId/:snapshotId1/:snapshotId2/statistics` - Get statistics about changes

### Social Media
- `GET /api/social/:archiveId` - Get social media posts related to an archive
- `GET /api/social/trending` - Get trending social media related to monitored sites

### Dashboard & Analytics
- `GET /api/stats/recent-changes` - Get recent significant changes
- `GET /api/stats/monitoring` - Get system monitoring statistics
- `GET /api/stats/summary` - Get summarized statistics across all archives

### System
- `GET /api/status` - Health check and status information
- `GET /api/config` - Get frontend configuration options

## Data Access Patterns

### PostgreSQL Integration
- Read-only access to the archiving system's database
- Dedicated read-replica if possible for performance isolation
- Optimized queries with proper indexing

### Caching Strategy
- Response caching with Redis:
  - Short TTL (1-5 minutes) for frequently changing data
  - Longer TTL (1-24 hours) for historical/static data
  - Cache invalidation on relevant archiving events

### Data Transformation
- Transform raw archive data into frontend-friendly formats
- Pre-calculate and cache complex statistics
- Optimize payload size for network efficiency

## Performance Considerations

### Response Time Optimization
- Implement pagination for large result sets
- Support field selection to reduce payload size
- Enable compression for all responses
- Use efficient serialization formats

### Scaling Strategy
- Stateless design for horizontal scaling
- Rate limiting to prevent abuse
- Query optimization for database efficiency

## Implementation Structure

```
govwatcher-api/
├── src/
│   ├── controllers/        # Request handlers
│   │   ├── archiveController.js
│   │   ├── diffController.js
│   │   ├── socialController.js
│   │   └── statsController.js
│   │
│   ├── services/          # Business logic
│   │   ├── archiveService.js
│   │   ├── diffService.js
│   │   ├── socialService.js
│   │   └── statsService.js
│   │
│   ├── models/            # Data models
│   │   ├── Archive.js
│   │   ├── Snapshot.js
│   │   ├── Diff.js
│   │   └── SocialPost.js
│   │
│   ├── middleware/        # Express middleware
│   │   ├── cache.js
│   │   ├── errorHandler.js
│   │   ├── rateLimiter.js
│   │   └── validator.js
│   │
│   ├── utils/             # Utility functions
│   │   ├── database.js
│   │   ├── cacheManager.js
│   │   └── responseFormatter.js
│   │
│   ├── config/            # Configuration
│   │   ├── database.js
│   │   ├── cache.js
│   │   └── server.js
│   │
│   ├── routes/            # API route definitions
│   │   ├── archiveRoutes.js
│   │   ├── diffRoutes.js
│   │   ├── socialRoutes.js
│   │   └── statsRoutes.js
│   │
│   └── app.js            # Application entry point
│
├── tests/                # Test suite
├── docs/                 # API documentation
├── package.json          # Dependencies
└── docker-compose.yml    # Development environment
```

## Database Access

The backend will access the archiving system's PostgreSQL database directly (read-only) for these tables:

- `archives` - Information about monitored websites
- `snapshots` - Individual website captures
- `diffs` - Stored differences between snapshots
- `social_posts` - Related social media content

## Deployment Considerations

### Container Configuration
- Lightweight Node.js or Python container
- Redis sidecar container for caching
- Resource limits aligned with expected load
- Direct mount of archive data volume (read-only)

### Environment Configuration
- Database connection details
- Cache settings
- CORS configuration for frontend access
- Archive data path configuration
- Logging levels

## Development Workflow

### Setup Process
1. Initialize Node.js/Express or Python/FastAPI project
2. Set up Docker development environment
3. Implement database access layer
4. Develop API endpoints incrementally
5. Add caching and optimization

### Testing Strategy
- Unit tests for services and utilities
- Integration tests for API endpoints
- Performance tests for critical paths
- Mock database for isolated testing

## Resource Requirements

### Minimal Production Environment
- 1-2 CPU cores
- 2-4GB RAM
- 20GB storage (mostly for logs and caching)

### Scaling Factors
- Number of concurrent users
- Number of archives being monitored
- Frequency of archive updates

## Security Considerations

### API Protection
- Rate limiting to prevent abuse
- Input validation for all parameters
- Output sanitization to prevent data leakage
- CORS configuration to restrict access

### Database Security
- Read-only access to production database
- Credentials management via environment variables
- Connection pooling with limits

## Implementation Plan

### Phase 1: Core API (1 week)
- Set up project structure and development environment
- Implement database connection
- Create basic archive and snapshot endpoints
- Establish testing framework

### Phase 2: Diff & Statistics API (1 week)
- Implement diff retrieval endpoints
- Add analytics and statistics endpoints
- Set up caching layer
- Optimize query performance

### Phase 3: Integration & Optimization (1 week)
- Connect with frontend for testing
- Implement advanced filtering and pagination
- Add documentation with OpenAPI/Swagger
- Performance tuning

### Phase 4: Advanced Features (as needed)
- Implement social media endpoints
- Add monitoring and alerting
- Set up production deployment

## Maintenance Considerations
- Log rotation and management
- Monitoring for performance issues
- Cache invalidation strategies
- Database connection management

## Future Enhancements
- GraphQL API for more flexible data retrieval
- Real-time notifications with WebSockets
- Advanced analytics endpoints
- Export functionality for reports 

## Integration with Archiving System

### Content Proxy Mechanism
The backend API will serve as a proxy for content stored in the archiving system:

1. **Content Retrieval Flow**:
   ```
   Frontend → Backend API → Archiving Content Server → WARC/Storage
   ```

2. **Content Transformation**:
   - The backend will transform content as needed before serving to frontend
   - Apply security headers and sanitization
   - Handle caching to reduce load on archiving system
   - Apply user-specific view preferences (if applicable)

3. **Snapshot Content Proxy**:
   For the endpoint `GET /api/archives/:id/snapshots/:snapshotId/content`:
   - The backend authenticates with the archiving system
   - Requests content from the archiving's content server
   - Streams response to frontend with appropriate caching headers
   - Handles content type detection and appropriate response headers

### Event-Based Notification Handling

The backend will implement webhook receivers to respond to archiving system events:

1. **Webhook Endpoints**:
   - `POST /webhooks/snapshot/created` - New snapshot available
   - `POST /webhooks/diff/generated` - New diff available
   - `POST /webhooks/change/detected` - Significant change detected

2. **Event Processing**:
   - Validate webhook authenticity using shared secrets
   - Update relevant cache entries
   - Trigger any real-time notifications

3. **Cache Invalidation Strategy**:
   - Selective invalidation based on event type
   - Update summary statistics and dashboard data
   - Preserve other cache entries to maintain performance

## Enhanced API Response Formats

To better support the frontend's needs, API responses will follow these patterns:

### Archive List Format
```json
{
  "data": [
    {
      "id": 123,
      "domain": "example.gov",
      "organization": "Example Agency",
      "lastChecked": "2023-04-15T12:30:45Z",
      "lastChanged": "2023-04-01T10:20:30Z",
      "changeCount": 5,
      "priority": "high",
      "status": "active"
    },
    // More archives
  ],
  "meta": {
    "total": 1250,
    "page": 1,
    "perPage": 20,
    "filterApplied": true
  }
}
```

### Snapshot Details Format
```json
{
  "id": 456,
  "archiveId": 123,
  "captureTimestamp": "2023-04-15T12:30:45Z",
  "status": 200,
  "size": 1523648,
  "formats": {
    "warc": true,
    "screenshot": true,
    "pdf": true,
    "text": true
  },
  "contentUrls": {
    "original": "/api/archives/123/snapshots/456/content?format=original",
    "screenshot": "/api/archives/123/snapshots/456/content?format=screenshot",
    "pdf": "/api/archives/123/snapshots/456/content?format=pdf"
  },
  "metadata": {
    "title": "Example.gov - Homepage",
    "description": "Official website of Example Agency",
    "contentType": "text/html",
    "headers": {
      // Key HTTP headers
    }
  }
}
```

### Diff Response Format
```json
{
  "id": 789,
  "archiveId": 123,
  "oldSnapshotId": 455,
  "newSnapshotId": 456,
  "oldTimestamp": "2023-04-01T10:20:30Z",
  "newTimestamp": "2023-04-15T12:30:45Z",
  "stats": {
    "additions": 35,
    "deletions": 12,
    "changes": 8,
    "significance": "major"
  },
  "diffData": {
    // Format compatible with react-diff-view
    "hunks": [
      {
        "content": "@@ -1,5 +1,8 @@",
        "oldStart": 1,
        "oldLines": 5,
        "newStart": 1,
        "newLines": 8,
        "changes": [
          // Change objects
        ]
      }
    ]
  },
  "visualDiff": {
    "screenshotDiff": "/api/diffs/789/screenshot",
    "highlightMap": [
      // Coordinates of changes
    ]
  }
}
```

## Synchronization with Archiving System

To ensure data consistency between the archiving system and backend API:

1. **Initial Synchronization**:
   - On startup, backend synchronizes its cache with current archiving system state
   - Preloads frequently accessed data for performance

2. **Periodic Reconciliation**:
   - Scheduled task verifies backend cache against archiving database
   - Repairs any inconsistencies found
   - Logs discrepancies for monitoring

3. **Database Access Optimization**:
   - Uses read replicas when possible
   - Implements connection pooling with appropriate limits
   - Monitors query performance

## Deployment Integration

To ensure smooth operation with other GovWatcher components:

### Docker Compose Integration
```yaml
version: '3'

services:
  frontend:
    image: govwatcher/frontend
    ports:
      - "80:80"
    depends_on:
      - api

  api:
    image: govwatcher/api
    environment:
      - DB_HOST=archive-db
      - DB_USER=api_readonly
      - DB_PASS=${API_DB_PASSWORD}
      - ARCHIVE_CONTENT_HOST=archive-content
      - REDIS_HOST=redis
    ports:
      - "3000:3000"
    depends_on:
      - archive-db
      - redis

  archive-system:
    image: govwatcher/archive
    volumes:
      - archive-data:/data
    environment:
      - DB_HOST=archive-db
      - DB_USER=archive_admin
      - DB_PASS=${ARCHIVE_DB_PASSWORD}
    depends_on:
      - archive-db

  archive-content:
    image: govwatcher/archive-content
    volumes:
      - archive-data:/data:ro
    environment:
      - DB_HOST=archive-db
      - DB_USER=content_readonly
      - DB_PASS=${CONTENT_DB_PASSWORD}
    depends_on:
      - archive-db

  archive-db:
    image: postgres:14
    volumes:
      - db-data:/var/lib/postgresql/data
    environment:
      - POSTGRES_PASSWORD=${DB_ROOT_PASSWORD}

  redis:
    image: redis:6
    volumes:
      - redis-data:/data

volumes:
  archive-data:
  db-data:
  redis-data:
``` 