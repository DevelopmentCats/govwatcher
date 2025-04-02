# GovWatcher Redis Plan

## Overview
This plan outlines the Redis implementation for GovWatcher, which serves multiple critical purposes within the system architecture. Redis will function as a caching layer, message broker, and job queue, helping to improve performance, reduce database load, and facilitate inter-component communication.

## Design Goals
- **Performance Optimization**: Cache frequently accessed data to reduce database load
- **Responsive UI**: Provide fast access to common queries and real-time updates
- **Component Communication**: Enable event-based communication between system components
- **Task Scheduling**: Implement reliable job queuing for archiving tasks
- **Resource Efficiency**: Optimize memory usage while maintaining performance

## Role in GovWatcher Architecture

Redis will serve three primary functions in the GovWatcher system:

1. **Caching Layer**:
   - API response caching
   - Frequently accessed archive metadata
   - User session data
   - Rendered diff visualizations

2. **Message Broker**:
   - Event publication for real-time updates
   - Notification system for significant changes
   - Webhook event processing queue

3. **Job Queue**:
   - Archiving task scheduling and prioritization
   - Background processing jobs
   - Retry mechanism for failed tasks

## Technical Implementation

### Redis Version & Configuration
- **Redis Version**: 6.2 or 7.0
- **Persistence**: RDB snapshots (every 15 minutes) + AOF (Append-Only File)
- **Memory Policy**: `volatile-lru` (evict least recently used keys with TTL)

### Resource Requirements
- **CPU**: 1-2 cores
- **RAM**: 2-4GB
- **Storage**: 10GB for persistence files
- **Network**: Low latency connection to API and Archive services

### Data Organization

We'll use a systematic key naming convention to organize data in Redis:

| Prefix | Purpose | Example Key | TTL |
|--------|---------|-------------|-----|
| `cache:` | General cached data | `cache:archives:list:page1` | 5 minutes |
| `stats:` | Analytics data | `stats:changes:daily:2023-04-15` | 1 hour |
| `session:` | User session data | `session:f7a9c4e2b3d1` | 24 hours |
| `lock:` | Distributed locks | `lock:archive:123` | 5 minutes |
| `queue:` | Task queues | `queue:archive:pending` | No expiry |
| `event:` | Event notifications | `event:changes:latest` | 1 hour |
| `rate:` | Rate limiting | `rate:ip:192.168.1.1` | 1 minute |

### Redis Data Structures

For different use cases, we'll leverage appropriate Redis data structures:

1. **String**: For simple key-value caching
   ```
   SET cache:archive:123 "{json data}" EX 300
   ```

2. **Hash**: For object properties
   ```
   HSET archive:123 domain "example.gov" agency "Example Agency" last_changed "2023-04-15T12:30:45Z"
   ```

3. **List**: For time-series data and queues
   ```
   LPUSH queue:archive:pending 123 456 789
   RPOP queue:archive:pending
   ```

4. **Sorted Set**: For priority queues and rankings
   ```
   ZADD queue:archive:priority 10 "archive:123" 5 "archive:456" 1 "archive:789"
   ```

5. **Set**: For unique collections
   ```
   SADD changed:today "archive:123" "archive:456"
   ```

## Caching Strategy

### API Response Caching

The backend API will use Redis to cache frequent responses:

```javascript
// Pseudocode for API caching middleware
async function cachingMiddleware(req, res, next) {
  const cacheKey = `cache:${req.path}:${querystring.stringify(req.query)}`;
  
  // Try to get from cache
  const cachedResponse = await redis.get(cacheKey);
  if (cachedResponse) {
    return res.json(JSON.parse(cachedResponse));
  }
  
  // Capture the response
  const originalSend = res.send;
  res.send = function(body) {
    // Cache the response with appropriate TTL based on endpoint
    const ttl = determineTTL(req.path);
    redis.set(cacheKey, body, 'EX', ttl);
    
    return originalSend.call(this, body);
  };
  
  next();
}
```

### Cache Invalidation Strategy

1. **Time-Based Expiration**:
   - Short TTL (1-5 minutes) for frequently changing data
   - Longer TTL (30-60 minutes) for relatively stable data
   - Very long TTL (24 hours) for historical/static content

2. **Event-Based Invalidation**:
   - Listen for change events from the archiving system
   - Selectively invalidate affected cache entries
   ```javascript
   // When a new snapshot is created
   function handleNewSnapshot(archiveId, snapshotId) {
     const patterns = [
       `cache:archives:${archiveId}*`,
       `cache:snapshots:${archiveId}*`,
       `stats:*`
     ];
     
     // Delete matching keys
     patterns.forEach(pattern => redis.del(pattern));
   }
   ```

3. **Prefix-Based Organization**:
   - Group related cache entries with shared prefixes
   - Enables targeted invalidation of specific data types

### Cache Warming

For predictable high-demand queries:

```javascript
// Daily cache warming job
async function warmCache() {
  // Pre-load frequent API responses
  const topArchives = await db.query('SELECT id FROM archives ORDER BY last_changed_at DESC LIMIT 20');
  
  for (const archive of topArchives) {
    // Queue requests that will populate the cache
    await fetchAndCacheArchive(archive.id);
  }
  
  // Warm dashboard stats
  await fetchAndCacheStats();
}
```

## Job Queue Implementation

Redis will power the archiving job queue:

### Queue Structure

We'll implement three queues with different priorities:

1. **High Priority Queue**: For immediate processing
   ```
   queue:archive:high
   ```

2. **Normal Priority Queue**: For regular scheduled jobs
   ```
   queue:archive:normal
   ```

3. **Low Priority Queue**: For background/bulk tasks
   ```
   queue:archive:low
   ```

### Job Processing Framework

We'll implement a reliable job processing system:

```javascript
// Pseudocode for the job processor
class ArchiveJobProcessor {
  constructor(redisClient) {
    this.redis = redisClient;
    this.processing = new Set();
  }
  
  async start() {
    // Process jobs in priority order
    while (true) {
      // Try to get job from high priority first, then normal, then low
      const job = await this.getNextJob();
      
      if (job) {
        try {
          this.processing.add(job.id);
          await this.processJob(job);
          await this.markJobComplete(job.id);
        } catch (error) {
          await this.handleJobFailure(job, error);
        } finally {
          this.processing.delete(job.id);
        }
      } else {
        // No jobs, wait briefly
        await sleep(1000);
      }
    }
  }
  
  async getNextJob() {
    // Check queues in priority order
    for (const priority of ['high', 'normal', 'low']) {
      const jobId = await this.redis.rpop(`queue:archive:${priority}`);
      if (jobId) {
        const jobData = await this.redis.hgetall(`job:${jobId}`);
        return { id: jobId, ...jobData };
      }
    }
    return null;
  }
  
  // Additional methods for job handling
}
```

### Job Scheduling

The archiving system will schedule jobs based on monitoring needs:

```javascript
// Pseudocode for job scheduling
async function scheduleArchiveJob(archiveId, priority = 'normal') {
  const jobId = generateUniqueId();
  
  // Store job details
  await redis.hset(`job:${jobId}`, {
    archiveId,
    status: 'pending',
    created: Date.now(),
    attempts: 0
  });
  
  // Add to appropriate queue
  await redis.lpush(`queue:archive:${priority}`, jobId);
  
  return jobId;
}
```

### Job Monitoring

We'll implement monitoring of job queue health:

```javascript
// Pseudocode for queue monitoring
async function getQueueStats() {
  const stats = {};
  
  for (const queue of ['high', 'normal', 'low']) {
    stats[queue] = {
      waiting: await redis.llen(`queue:archive:${queue}`),
      processing: await getProcessingCount(queue)
    };
  }
  
  // Get statistics on job completion
  stats.completed = await redis.get('stats:jobs:completed') || 0;
  stats.failed = await redis.get('stats:jobs:failed') || 0;
  
  return stats;
}
```

## Event Notification System

Redis Pub/Sub will power real-time notifications:

### Event Channels

We'll create specific channels for different event types:

1. **Archive Updates**:
   ```
   channel:archive:updated
   ```

2. **Significant Changes**:
   ```
   channel:changes:significant
   ```

3. **System Status**:
   ```
   channel:system:status
   ```

### Publisher Implementation

The archiving system will publish events when significant changes occur:

```javascript
// Pseudocode for publishing events
async function publishArchiveUpdate(archiveId, changeType, details) {
  const event = {
    type: changeType,
    archiveId,
    timestamp: new Date().toISOString(),
    details
  };
  
  await redis.publish('channel:archive:updated', JSON.stringify(event));
  
  // If it's a significant change, publish to that channel too
  if (isSignificantChange(details)) {
    await redis.publish('channel:changes:significant', JSON.stringify(event));
  }
}
```

### Subscriber Implementation

The API service will subscribe to relevant channels:

```javascript
// Pseudocode for event subscription
function subscribeToEvents(redisClient) {
  const subscriber = redisClient.duplicate();
  
  subscriber.subscribe('channel:archive:updated');
  subscriber.subscribe('channel:changes:significant');
  
  subscriber.on('message', (channel, message) => {
    const event = JSON.parse(message);
    
    switch (channel) {
      case 'channel:archive:updated':
        handleArchiveUpdate(event);
        break;
      case 'channel:changes:significant':
        handleSignificantChange(event);
        break;
    }
  });
}

function handleArchiveUpdate(event) {
  // Invalidate relevant cache entries
  invalidateCacheForArchive(event.archiveId);
  
  // Notify connected clients if using WebSockets
  notifyClients('archive-updated', event);
}
```

## Docker Configuration

```dockerfile
FROM redis:6.2-alpine

# Copy custom configuration
COPY redis.conf /usr/local/etc/redis/redis.conf

# Create directory for persistence
RUN mkdir -p /data

# Set appropriate permissions
RUN chown redis:redis /data

# Expose Redis port
EXPOSE 6379

# Set default command
CMD ["redis-server", "/usr/local/etc/redis/redis.conf"]
```

## Redis Configuration File

```
# redis.conf

# Basic configuration
port 6379
bind 0.0.0.0
protected-mode yes

# Memory management
maxmemory 2gb
maxmemory-policy volatile-lru
maxmemory-samples 5

# Persistence configuration
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb
dir /data

# AOF configuration
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec

# Performance tuning
tcp-keepalive 300
timeout 0
tcp-backlog 511
databases 16

# Logging
loglevel notice
logfile ""

# Security
requirepass ${REDIS_PASSWORD}
```

## Performance Optimization

### Memory Optimization
- Use hashes for structured data instead of storing serialized objects
- Implement key expiration for all cached items
- Monitor memory usage and adjust maxmemory setting
- Use Redis Stream instead of Lists for high-volume event logging

### Connection Management
- Implement connection pooling for API and Archive service
- Set appropriate connection limits
- Use pipeline commands for batch operations
- Monitor connected clients and prevent connection leaks

### Command Optimization
- Use SCAN instead of KEYS for production environments
- Avoid expensive operations like SORT on large datasets
- Utilize MULTI/EXEC for transaction guarantees when needed
- Leverage server-side Lua scripting for complex operations

## Monitoring and Maintenance

### Health Checks
- Regular PING command to verify service availability
- Monitor memory usage and eviction rates
- Track hit/miss ratio for cache effectiveness
- Monitor connected clients and command processing rates

### Redis Commands for Monitoring

```bash
# Check memory usage
redis-cli INFO memory

# Monitor cache hit rate
redis-cli INFO stats | grep -E 'keyspace_hits|keyspace_misses'

# Check client connections
redis-cli CLIENT LIST | wc -l

# Monitor job queue size
redis-cli LLEN queue:archive:normal
```

### Integration with Monitoring Systems
- Export Redis metrics to Prometheus
- Create Grafana dashboards for visualizing Redis performance
- Set up alerts for critical conditions:
  - High memory usage (>80%)
  - High eviction rate
  - Connection saturation
  - Error rates

## Integration with Other Components

### Archive System Integration
- Job queue for scheduling archiving tasks
- Event publication for completed archives
- Locking mechanism for distributed operations

### API Integration
- Response caching for frequently accessed endpoints
- Session storage for user preferences
- Event subscription for real-time updates
- Rate limiting implementation

### Frontend Integration
- WebSocket notifications powered by Redis Pub/Sub
- Client-side caching coordination
- User activity tracking

## Security Considerations

### Access Control
- Use strong Redis authentication password
- Network-level access restrictions
- Configure Redis to bind only to internal interfaces

### Data Protection
- Avoid storing sensitive information as plain text
- Implement key prefix namespacing to prevent conflicts
- Regular backup of persistence files

### Connection Security
- Use TLS for Redis connections if exposed beyond trusted network
- Implement connection timeouts
- Limit maximum number of clients

## Backup Strategy

1. **RDB Snapshots**:
   - Automatic snapshots every 15 minutes
   - Copy snapshot files to backup storage

2. **AOF Persistence**:
   - Enable appendonly mode for write operation logging
   - Regular AOF rewriting to prevent file growth

3. **Backup Rotation**:
   - Daily backups retained for 7 days
   - Weekly backups retained for 4 weeks

## Development Workflow

### Local Setup
- Docker Compose configuration for development
- Local Redis instance with development configuration
- Tools for inspecting Redis data during development

### Testing
- Mock Redis service for unit tests
- Integration tests using test Redis instance
- Load testing for cache performance

## Future Enhancements

1. **Redis Cluster**
   - Implement Redis Cluster for horizontal scaling
   - Shard data across multiple Redis nodes
   - Increase resilience through replication

2. **Redis Modules**
   - RediSearch for full-text search capabilities
   - RedisTimeSeries for efficient time-series data
   - RedisGraph for relationship data (if needed)

3. **Advanced Analytics**
   - Implement counters for real-time statistics
   - Use Redis for tracking trending content
   - Create real-time dashboards

4. **Intelligent Caching**
   - Machine learning-based cache warming
   - Predictive invalidation of cache entries
   - Adaptive TTL based on data access patterns 