FROM redis:6.2-alpine

# Copy custom Redis configuration
COPY redis.conf /usr/local/etc/redis/redis.conf

# Create directory for persistence
RUN mkdir -p /data && \
    chown redis:redis /data

# Expose Redis port
EXPOSE 6379

# Command to run Redis with custom configuration
CMD ["redis-server", "/usr/local/etc/redis/redis.conf"] 