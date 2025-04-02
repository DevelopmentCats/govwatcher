# GovWatcher Deployment Plan

## Overview
This document outlines the complete deployment strategy for the GovWatcher system, which consists of five main components: Frontend, API, Archive System, PostgreSQL Database, and Redis. The plan covers initial setup, continuous deployment, monitoring, scaling, and maintenance procedures.

## System Requirements

### Production Environment

#### Hardware Requirements
- **Server Type**: Virtual or bare metal with Linux OS (Ubuntu 20.04 LTS or newer)
- **CPU**: 8+ cores (minimum)
  - Archive System: 4 cores
  - API: 1-2 cores
  - Database: 2 cores
  - Redis: 1 core
  - Frontend: Minimal (static content)
- **RAM**: 16GB+ (minimum)
  - Archive System: 8GB
  - API: 2-4GB
  - Database: 4GB
  - Redis: 2GB
  - Frontend: Minimal (static content)
- **Storage**:
  - Archive Data: 1TB+ SSD/NVMe for archived content (expandable)
  - Database: 50GB SSD
  - System: 20GB
  - Logs: 10GB
- **Network**: 100Mbps+ internet connection, preferably with static IP

#### Software Requirements
- Docker Engine (20.10+)
- Docker Compose V2 (part of Docker Engine)
- Nginx (for reverse proxy, SSL termination)
- Let's Encrypt for SSL certificates
- Git for deployment

### Development/Staging Environment
- Scaled-down version of production with similar architecture
- Minimum 4 CPU cores, 8GB RAM, 100GB storage

## Deployment Architecture

```
                           ┌────────────────────────────────┐
                           │        Load Balancer/          │
                           │        Reverse Proxy           │
                           │        (Nginx/Traefik)         │
                           └───────────────┬────────────────┘
                                           │
                                           ▼
                     ┌─────────────────────────────────────────┐
                     │                                         │
        ┌────────────┴──────────────┐              ┌───────────┴────────────┐
        │                           │              │                         │
        ▼                           ▼              ▼                         ▼
┌─────────────────┐        ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    Frontend     │◄───────┤      API        │◄───┤  Archive System  │    │  Monitoring     │
│    Container    │        │    Container    │    │    Container     │    │   (Prometheus/  │
└─────────────────┘        └────────┬────────┘    └────────┬─────────┘    │    Grafana)     │
                                    │                      │              └─────────────────┘
                                    │                      │
                                    ▼                      ▼
                           ┌─────────────────┐    ┌─────────────────┐
                           │    Database     │◄───┤     Redis       │
                           │    Container    │    │    Container    │
                           └─────────────────┘    └─────────────────┘
                                    ▲                      ▲
                                    │                      │
                                    ▼                      ▼
                           ┌─────────────────┐    ┌─────────────────┐
                           │  Database Data  │    │   Redis Data    │
                           │     Volume      │    │     Volume      │
                           └─────────────────┘    └─────────────────┘
                                                          ▲
                                                          │
                                                          ▼
                                                 ┌─────────────────┐
                                                 │  Archive Data   │
                                                 │     Volume      │
                                                 └─────────────────┘
```

## Initial Deployment Procedure

### 1. Server Preparation

1. **Base Server Setup**:
   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y
   
   # Install required packages
   sudo apt install -y apt-transport-https ca-certificates curl software-properties-common git nginx
   
   # Install Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   
   # Add user to docker group
   sudo usermod -aG docker $USER
   
   # Ensure Docker Compose V2 is installed (included in Docker Engine)
   docker compose version
   
   # Create necessary directories
   sudo mkdir -p /opt/govwatcher
   sudo mkdir -p /data/govwatcher/archive-data
   sudo mkdir -p /data/govwatcher/db-data
   sudo mkdir -p /data/govwatcher/redis-data
   sudo mkdir -p /data/govwatcher/logs
   sudo mkdir -p /data/govwatcher/backups
   
   # Set proper permissions
   sudo chown -R $USER:$USER /opt/govwatcher
   sudo chown -R $USER:$USER /data/govwatcher
   ```

2. **Clone Repository**:
   ```bash
   cd /opt/govwatcher
   git clone https://github.com/yourusername/govwatcher.git .
   ```

3. **Set Up Environment Variables**:
   ```bash
   # Create .env file from template
   cp .env.example .env
   
   # Edit the .env file with secure values
   nano .env
   ```

4. **Configure Storage Volumes**:
   ```bash
   # Edit docker-compose.yml to map to correct host paths
   nano docker-compose.yml
   
   # Update volume paths to match host configuration
   # Example:
   # volumes:
   #   archive-data:
   #     driver: local
   #     driver_opts:
   #       type: none
   #       device: /data/govwatcher/archive-data
   #       o: bind
   ```

### 2. Network and Security Configuration

1. **Configure Firewall**:
   ```bash
   # Allow SSH, HTTP, and HTTPS
   sudo ufw allow 22
   sudo ufw allow 80
   sudo ufw allow 443
   
   # Enable the firewall
   sudo ufw enable
   ```

2. **Set Up Nginx as Reverse Proxy**:
   ```bash
   # Create Nginx config
   sudo nano /etc/nginx/sites-available/govwatcher
   
   # Add configuration (example):
   # server {
   #     listen 80;
   #     server_name govwatcher.yourdomain.com;
   #
   #     location / {
   #         proxy_pass http://localhost:80;
   #         proxy_set_header Host $host;
   #         proxy_set_header X-Real-IP $remote_addr;
   #     }
   #
   #     location /api {
   #         proxy_pass http://localhost:3000;
   #         proxy_set_header Host $host;
   #         proxy_set_header X-Real-IP $remote_addr;
   #     }
   # }
   
   # Enable the site
   sudo ln -s /etc/nginx/sites-available/govwatcher /etc/nginx/sites-enabled/
   
   # Test and reload Nginx
   sudo nginx -t
   sudo systemctl reload nginx
   ```

3. **Set Up SSL with Let's Encrypt**:
   ```bash
   # Install Certbot
   sudo apt install -y certbot python3-certbot-nginx
   
   # Obtain SSL certificate
   sudo certbot --nginx -d govwatcher.yourdomain.com
   
   # Set up auto-renewal
   sudo systemctl status certbot.timer
   ```

### 3. Database Initialization

1. **Initialize Database**:
   ```bash
   # Navigate to project directory
   cd /opt/govwatcher
   
   # Start the database container first
   docker compose up -d db
   
   # Wait for database to initialize
   sleep 30
   
   # Verify database is running
   docker compose logs db
   ```

2. **Verify Database Initialization**:
   ```bash
   # Connect to database to verify initialization
   docker compose exec db psql -U postgres -d govwatcher -c "\dt"
   
   # Should show all tables created from initialization scripts
   ```

### 4. Deploy Full System

1. **Start All Services**:
   ```bash
   # Deploy all containers
   docker compose up -d
   
   # Check status
   docker compose ps
   
   # View logs
   docker compose logs
   ```

2. **Initialize Archive System**:
   ```bash
   # Run the initialization script
   docker compose exec archive python setup.py --source-csv=current-full.csv --priority-csv=current-federal.csv
   ```

3. **Verify Deployment**:
   ```bash
   # Check each service
   curl -I http://localhost
   curl -I http://localhost:3000/api/status
   
   # Check database connection
   docker compose exec api node -e "const db = require('./src/utils/database'); db.testConnection().then(console.log).catch(console.error);"
   ```

## Continuous Deployment Pipeline

### 1. CI/CD Setup (GitHub Actions example)

Create a `.github/workflows/deploy.yml` file:

```yaml
name: Deploy GovWatcher

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v2

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v1

      - name: Login to DockerHub
        uses: docker/login-action@v1
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Build and push Frontend
        uses: docker/build-push-action@v2
        with:
          context: ./govwatcher-frontend
          push: true
          tags: yourusername/govwatcher-frontend:latest

      - name: Build and push API
        uses: docker/build-push-action@v2
        with:
          context: ./govwatcher-api
          push: true
          tags: yourusername/govwatcher-api:latest

      - name: Build and push Archive System
        uses: docker/build-push-action@v2
        with:
          context: ./govwatcher-archive
          push: true
          tags: yourusername/govwatcher-archive:latest

      - name: Deploy to production server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.DEPLOY_HOST }}
          username: ${{ secrets.DEPLOY_USER }}
          key: ${{ secrets.DEPLOY_KEY }}
          script: |
            cd /opt/govwatcher
            git pull
            docker compose pull
            docker compose up -d
```

### 2. Deployment Scripts

Create a `deploy.sh` script for manual deployment:

```bash
#!/bin/bash
# GovWatcher deployment script

# Load environment variables
source .env

# Pull latest code
git pull

# Build or pull containers
docker compose pull

# Bring down system with minimal downtime
docker compose down --remove-orphans

# Start services in correct order
docker compose up -d db redis
sleep 10
docker compose up -d archive api
sleep 5
docker compose up -d frontend

# Verify deployment
docker compose ps
```

## Backup Strategy

### 1. Database Backup

Create a `backup_db.sh` script:

```bash
#!/bin/bash
# Database backup script

BACKUP_DIR="/data/govwatcher/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/db_backup_$TIMESTAMP.sql.gz"

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

# Create backup
docker compose exec -T db pg_dump -U postgres -d govwatcher | gzip > $BACKUP_FILE

# Rotate backups - keep last 14 days
find $BACKUP_DIR -name "db_backup_*.sql.gz" -type f -mtime +14 -delete

# Log backup completion
echo "Database backup completed at $TIMESTAMP - $BACKUP_FILE" >> $BACKUP_DIR/backup_log.txt
```

### 2. Archive Data Backup

Create a `backup_archives.sh` script:

```bash
#!/bin/bash
# Archive data backup script

BACKUP_DIR="/data/govwatcher/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ARCHIVE_DATA_DIR="/data/govwatcher/archive-data"
BACKUP_FILE="$BACKUP_DIR/archive_backup_$TIMESTAMP.tar.gz"

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

# Create backup of archive data
tar -czf $BACKUP_FILE -C $ARCHIVE_DATA_DIR .

# Rotate backups - keep last 7 days for full backups
find $BACKUP_DIR -name "archive_backup_*.tar.gz" -type f -mtime +7 -delete

# Log backup completion
echo "Archive backup completed at $TIMESTAMP - $BACKUP_FILE" >> $BACKUP_DIR/backup_log.txt
```

### 3. Set Up Cron Jobs for Automated Backups

```bash
# Edit crontab
crontab -e

# Add backup jobs
# Database: Daily at 1:00 AM
0 1 * * * /opt/govwatcher/backup_db.sh > /dev/null 2>&1

# Archive data: Weekly on Sunday at 2:00 AM
0 2 * * 0 /opt/govwatcher/backup_archives.sh > /dev/null 2>&1
```

## Monitoring Setup

### 1. Set Up Basic Monitoring with Prometheus and Grafana

Add monitoring services to `docker-compose.yml`:

```yaml
# Prometheus for metrics collection
prometheus:
  image: prom/prometheus
  container_name: govwatcher-prometheus
  volumes:
    - ./monitoring/prometheus:/etc/prometheus
    - prometheus-data:/prometheus
  command:
    - '--config.file=/etc/prometheus/prometheus.yml'
    - '--storage.tsdb.path=/prometheus'
    - '--web.console.libraries=/etc/prometheus/console_libraries'
    - '--web.console.templates=/etc/prometheus/consoles'
  ports:
    - "9090:9090"
  restart: unless-stopped
  networks:
    - govwatcher-network

# Grafana for visualization
grafana:
  image: grafana/grafana
  container_name: govwatcher-grafana
  volumes:
    - grafana-data:/var/lib/grafana
    - ./monitoring/grafana/provisioning:/etc/grafana/provisioning
  environment:
    - GF_SECURITY_ADMIN_USER=${GRAFANA_ADMIN_USER:-admin}
    - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD:-admin}
    - GF_USERS_ALLOW_SIGN_UP=false
  ports:
    - "3001:3000"
  restart: unless-stopped
  networks:
    - govwatcher-network
```

### 2. Configure Log Collection

Add log collection with Filebeat:

```yaml
# Filebeat for log collection
filebeat:
  image: docker.elastic.co/beats/filebeat:7.15.0
  container_name: govwatcher-filebeat
  volumes:
    - ./monitoring/filebeat/filebeat.yml:/usr/share/filebeat/filebeat.yml:ro
    - /var/lib/docker/containers:/var/lib/docker/containers:ro
    - /var/run/docker.sock:/var/run/docker.sock:ro
    - filebeat-data:/usr/share/filebeat/data
  user: root
  restart: unless-stopped
  networks:
    - govwatcher-network
```

### 3. Configure Alerting

1. Set up Grafana alerting to notify of system issues
2. Configure email/Slack/PagerDuty notifications

## Scaling Strategy

### 1. Vertical Scaling

For initial growth, increase resources on the existing server:

- Increase CPU/RAM allocation for Docker containers
- Update resource limits in docker-compose.yml

### 2. Horizontal Scaling

For substantial growth:

1. **Frontend**:
   - Deploy multiple instances behind a load balancer
   - Use a CDN for static assets

2. **API**:
   - Deploy multiple instances behind a load balancer
   - Ensure proper session handling for stateless operation

3. **Archive System**:
   - Distribute crawling across multiple workers
   - Implement work queue distribution

4. **Database**:
   - Set up read replicas for API queries
   - Consider sharding for very large datasets

5. **Redis**:
   - Implement Redis Cluster for distributed caching
   - Separate instances by function (cache, queue, pubsub)

### 3. Container Orchestration Migration

For large-scale deployments:

1. Convert docker-compose.yml to Kubernetes manifests
2. Set up a managed Kubernetes cluster
3. Implement proper resource requests/limits and auto-scaling

## Maintenance Procedures

### 1. Regular Updates

Schedule regular maintenance windows for:

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Docker images
docker compose pull
docker compose up -d

# Clean up unused images and volumes
docker system prune -f
```

### 2. Database Maintenance

Schedule regular database maintenance:

```bash
# Connect to database
docker compose exec db psql -U postgres -d govwatcher

# Run VACUUM ANALYZE
VACUUM ANALYZE;

# Check table sizes
SELECT relname, pg_size_pretty(pg_total_relation_size(relid)) 
FROM pg_catalog.pg_statio_user_tables 
ORDER BY pg_total_relation_size(relid) DESC;
```

### 3. Log Rotation

Ensure proper log rotation:

```bash
# Set up log rotation for Docker
sudo nano /etc/logrotate.d/docker-container
# Add:
# /var/lib/docker/containers/*/*.log {
#   rotate 7
#   daily
#   compress
#   missingok
#   delaycompress
#   copytruncate
# }
```

## Disaster Recovery Plan

### 1. Failure Scenarios and Recovery Procedures

| Scenario | Detection Method | Recovery Procedure |
|----------|------------------|-------------------|
| Server hardware failure | Monitoring alert | 1. Provision new server<br>2. Install Docker/dependencies<br>3. Restore from latest backups<br>4. Update DNS if needed |
| Database corruption | Query errors, consistency checks | 1. Stop dependent services<br>2. Restore from latest backup<br>3. Restart services |
| Storage full | Disk space monitoring | 1. Extend volume/disk space<br>2. Clean up unused data<br>3. Consider data archiving policy |
| Container failure | Docker health checks | 1. Check container logs<br>2. Restart container<br>3. If persistent, restore from backup |

### 2. Recovery Testing

Regularly test recovery procedures:

1. Schedule quarterly disaster recovery tests
2. Document recovery time and any issues encountered
3. Update procedures based on test results

## Security Considerations

### 1. Regular Security Updates

```bash
# Update system security packages
sudo apt update && sudo apt install --only-upgrade security

# Review Docker security
docker info | grep -i seccomp
docker info | grep -i apparmor
```

### 2. Access Control

- Use least-privilege principle for all services
- Implement strong password policies
- Consider setting up VPN for administrative access

### 3. Data Security

- Encrypt sensitive data at rest
- Implement proper database user permissions
- Regular security audits

## Documentation

### 1. System Documentation

- Maintain updated architecture diagrams
- Document all custom configurations
- Keep detailed deployment notes

### 2. Runbooks

Create operational runbooks for:
- Deployment
- Scaling
- Backups and recovery
- Common troubleshooting

### 3. Knowledge Base

- Document common issues and solutions
- Create FAQ for operations team

## Estimated Timeline

| Phase | Tasks | Timeline |
|-------|-------|----------|
| Infrastructure Setup | Server provisioning, Docker installation, network config | Week 1 |
| Initial Deployment | Database setup, component deployment, data initialization | Week 2 |
| Monitoring Setup | Prometheus, Grafana, alerting configuration | Week 3 |
| Testing | Load testing, security testing, recovery testing | Week 4 |
| Go-Live | Production deployment, initial monitoring | Week 5 |
| Post-Deployment | Optimizations, documentation completion | Week 6 |

## Appendix

### Environment Variables Reference

Create a `.env` file with these variables:

```
# Database credentials
DB_ROOT_PASSWORD=secure_postgres_root_password
API_DB_PASSWORD=secure_api_db_password
ARCHIVE_DB_PASSWORD=secure_archive_db_password
READONLY_DB_PASSWORD=secure_readonly_password

# Redis configuration
REDIS_PASSWORD=secure_redis_password

# API configuration
NODE_ENV=production
API_PORT=3000

# Archive system configuration
ARCHIVE_CONCURRENCY=3
ARCHIVE_PRIORITY_THRESHOLD=5

# Monitoring
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=secure_grafana_password

# Domain configuration
DOMAIN_NAME=govwatcher.yourdomain.com
```

### Docker Compose Override Example

Create a `docker-compose.override.yml` for development:

```yaml
version: '3.8'

services:
  frontend:
    build:
      context: ./govwatcher-frontend
      dockerfile: Dockerfile.dev
    volumes:
      - ./govwatcher-frontend:/app
      - /app/node_modules
    command: npm run dev

  api:
    build:
      context: ./govwatcher-api
      dockerfile: Dockerfile.dev
    volumes:
      - ./govwatcher-api:/app
      - /app/node_modules
    command: npm run dev

  archive:
    build:
      context: ./govwatcher-archive
      dockerfile: Dockerfile.dev
    volumes:
      - ./govwatcher-archive:/app
      - /app/__pycache__
    command: python run.py --dev
``` 