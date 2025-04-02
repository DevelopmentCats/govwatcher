"""
Redis client for the archiving system.
Handles queue management, caching, and pub/sub.
"""
import json
import time
import logging
import redis

logger = logging.getLogger('govwatcher-archive.redis')

class RedisClient:
    """Redis client wrapper with utility functions"""
    
    def __init__(self, host, port, password=None, db=0):
        """Initialize Redis connection"""
        self.conn_params = {
            'host': host,
            'port': port,
            'password': password,
            'db': db,
            'decode_responses': True,  # Return strings instead of bytes
        }
        self.redis = None
        self.connect()
    
    def connect(self):
        """Establish Redis connection"""
        try:
            self.redis = redis.Redis(**self.conn_params)
            self.redis.ping()  # Test connection
            logger.info("Redis connection established")
        except redis.RedisError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    def close(self):
        """Close Redis connection"""
        if self.redis:
            self.redis.close()
            logger.info("Redis connection closed")
    
    def get_client(self):
        """Get the Redis client instance"""
        return self.redis
    
    # Queue Management
    
    def enqueue_job(self, queue_name, job_data, priority=5):
        """Add a job to a priority queue"""
        job_id = f"job:{int(time.time())}:{job_data.get('id', '')}"
        
        # Store job data
        job_key = f"jobs:{job_id}"
        self.redis.hset(job_key, mapping={
            'status': 'pending',
            'priority': priority,
            'created_at': int(time.time()),
            'data': json.dumps(job_data)
        })
        
        # Add to priority queue
        self.redis.zadd(f"queue:{queue_name}", {job_id: priority})
        
        logger.debug(f"Job {job_id} added to queue {queue_name} with priority {priority}")
        return job_id
    
    def get_next_job(self, queue_name):
        """Get the next job from a priority queue"""
        # Get job with highest priority (lowest score)
        result = self.redis.zpopmin(f"queue:{queue_name}", count=1)
        if not result:
            return None
        
        job_id, _ = result[0]  # Unpack the (job_id, score) tuple
        
        # Get job data
        job_key = f"jobs:{job_id}"
        job_data = self.redis.hgetall(job_key)
        
        if not job_data:
            logger.warning(f"Job {job_id} not found in Redis")
            return None
        
        # Update job status
        self.redis.hset(job_key, 'status', 'processing')
        self.redis.hset(job_key, 'started_at', int(time.time()))
        
        # Add to processing set
        self.redis.sadd(f"processing:{queue_name}", job_id)
        
        try:
            # Parse job data
            data = json.loads(job_data.get('data', '{}'))
            return {
                'id': job_id,
                'priority': int(job_data.get('priority', 5)),
                'created_at': int(job_data.get('created_at', 0)),
                'data': data
            }
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse job data: {e}")
            return None
    
    def complete_job(self, queue_name, job_id, result=None):
        """Mark a job as completed"""
        job_key = f"jobs:{job_id}"
        
        # Update job status
        self.redis.hset(job_key, 'status', 'completed')
        self.redis.hset(job_key, 'completed_at', int(time.time()))
        
        if result:
            self.redis.hset(job_key, 'result', json.dumps(result))
        
        # Remove from processing set
        self.redis.srem(f"processing:{queue_name}", job_id)
        
        # Increment completed counter
        self.redis.incr(f"stats:{queue_name}:completed")
        
        logger.debug(f"Job {job_id} marked as completed")
    
    def fail_job(self, queue_name, job_id, error=None, retry=False, max_retries=3):
        """Mark a job as failed and optionally requeue"""
        job_key = f"jobs:{job_id}"
        
        # Get current retry count
        retries = int(self.redis.hget(job_key, 'retries') or 0)
        
        if retry and retries < max_retries:
            # Increment retry count
            self.redis.hincrby(job_key, 'retries', 1)
            self.redis.hset(job_key, 'last_error', str(error) if error else 'Unknown error')
            
            # Get job priority
            priority = int(self.redis.hget(job_key, 'priority') or 5)
            
            # Add back to queue with adjusted priority
            self.redis.zadd(f"queue:{queue_name}", {job_id: priority + 1})
            self.redis.hset(job_key, 'status', 'pending')
            
            logger.info(f"Job {job_id} requeued for retry {retries + 1}/{max_retries}")
        else:
            # Mark as failed
            self.redis.hset(job_key, 'status', 'failed')
            self.redis.hset(job_key, 'failed_at', int(time.time()))
            
            if error:
                self.redis.hset(job_key, 'error', str(error))
            
            # Increment failed counter
            self.redis.incr(f"stats:{queue_name}:failed")
            
            logger.warning(f"Job {job_id} marked as failed: {error}")
        
        # Remove from processing set
        self.redis.srem(f"processing:{queue_name}", job_id)
    
    def get_queue_stats(self, queue_name):
        """Get statistics for a queue"""
        pending = self.redis.zcard(f"queue:{queue_name}")
        processing = self.redis.scard(f"processing:{queue_name}")
        completed = int(self.redis.get(f"stats:{queue_name}:completed") or 0)
        failed = int(self.redis.get(f"stats:{queue_name}:failed") or 0)
        
        return {
            'pending': pending,
            'processing': processing,
            'completed': completed,
            'failed': failed,
            'total': pending + processing + completed + failed
        }
    
    # Caching
    
    def cache_set(self, key, value, ttl=300):
        """Set a cached value with TTL"""
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        
        self.redis.set(f"cache:{key}", value, ex=ttl)
    
    def cache_get(self, key, default=None):
        """Get a cached value"""
        value = self.redis.get(f"cache:{key}")
        
        if value is None:
            return default
        
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    
    def cache_delete(self, key):
        """Delete a cached value"""
        self.redis.delete(f"cache:{key}")
    
    def cache_invalidate_pattern(self, pattern):
        """Invalidate all cache keys matching a pattern"""
        keys = self.redis.keys(f"cache:{pattern}")
        if keys:
            self.redis.delete(*keys)
            logger.debug(f"Invalidated {len(keys)} cache keys matching pattern '{pattern}'")
    
    # Pub/Sub
    
    def publish(self, channel, message):
        """Publish a message to a channel"""
        if isinstance(message, (dict, list)):
            message = json.dumps(message)
        
        self.redis.publish(channel, message)
        logger.debug(f"Published message to channel '{channel}'")
    
    def subscribe(self, channel):
        """Create a new Redis client and subscribe to a channel"""
        pubsub = self.redis.pubsub()
        pubsub.subscribe(channel)
        return pubsub
    
    # Distributed Locks
    
    def acquire_lock(self, name, timeout=10, expire=60):
        """Acquire a distributed lock"""
        lock_key = f"lock:{name}"
        identifier = str(time.time())
        
        deadline = time.time() + timeout
        while time.time() < deadline:
            # Try to acquire the lock
            if self.redis.set(lock_key, identifier, ex=expire, nx=True):
                logger.debug(f"Acquired lock '{name}'")
                return identifier
            
            # Wait before retrying
            time.sleep(0.1)
        
        logger.warning(f"Failed to acquire lock '{name}' after {timeout} seconds")
        return None
    
    def release_lock(self, name, identifier):
        """Release a distributed lock"""
        lock_key = f"lock:{name}"
        
        # Only release if we own the lock
        script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        
        result = self.redis.eval(script, 1, lock_key, identifier)
        if result:
            logger.debug(f"Released lock '{name}'")
            return True
        
        logger.warning(f"Failed to release lock '{name}': not the owner")
        return False 