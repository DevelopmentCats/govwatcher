# GovWatcher Archive System

The GovWatcher Archive System is a component of the GovWatcher platform that archives and tracks changes to government websites over time.

## Features

- Scheduled archiving of .gov websites
- Change detection and visual diff generation
- Archive storage and management
- REST API integration for accessing archived content

## Installation

### Prerequisites

- Docker and Docker Compose
- Python 3.9+
- PostgreSQL database
- Redis server

### Setup with Docker

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/govwatcher.git
   cd govwatcher/govwatcher-archive
   ```

2. Create a `.env` file with your configuration:
   ```
   DB_HOST=db
   DB_PORT=5432
   DB_NAME=govwatcher
   DB_USER=archive_admin
   DB_PASSWORD=your_secure_password
   
   REDIS_HOST=redis
   REDIS_PORT=6379
   REDIS_PASSWORD=your_redis_password
   ```

3. Start the services:
   ```bash
   docker compose up -d
   ```

### Local Development Setup

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up the database:
   ```bash
   # Run SQL scripts to create required tables
   ```

3. Run the application:
   ```bash
   python src/main.py server
   ```

## Usage

### Command Line Interface

The archiving system provides a command-line interface for various operations:

```bash
# Run the archiving server
python src/main.py server

# Import domains from a CSV file
python src/main.py import --file domains.csv --priority-file federal.csv

# Crawl a specific domain
python src/main.py crawl --domain example.gov

# Generate a diff between two snapshots
python src/main.py diff --archive-id 123 --snapshot1 456 --snapshot2 789
```

### Docker Usage

When using Docker, prefix the commands with `docker compose exec archive`:

```bash
docker compose exec archive python src/main.py import --file domains.csv
```

## Architecture

The archiving system consists of several components:

- **Main Application**: Coordinates the archiving process
- **Crawler**: Captures website content
- **Storage Manager**: Manages file storage
- **Diff Processor**: Generates diffs between snapshots
- **Database**: Stores metadata and references to files

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -am 'Add my feature'`
4. Push to the branch: `git push origin feature/my-feature`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
