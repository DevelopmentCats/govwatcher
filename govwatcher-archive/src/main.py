#!/usr/bin/env python3
"""
GovWatcher Archiving System
Main entry point for the application.
"""
import os
import sys
import logging
import argparse
import signal
import time
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('govwatcher-archive')

# Import project modules
try:
    from config import Config
    from crawlers import CrawlerManager
    from processors import DiffProcessor
    from storage import StorageManager
    from utils.db import Database
    from utils.redis_client import RedisClient
    from models.archive import Archive
    from models.snapshot import Snapshot
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    sys.exit(1)

def signal_handler(sig, frame):
    """Handle graceful shutdown on SIGINT/SIGTERM"""
    logger.info("Shutdown signal received, exiting gracefully...")
    sys.exit(0)

def setup():
    """Initialize the application"""
    # Load environment variables
    load_dotenv()
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Initialize configuration
    config = Config()
    
    # Initialize connections
    try:
        db = Database(
            host=os.getenv('DB_HOST', 'db'),
            port=int(os.getenv('DB_PORT', '5432')),
            database=os.getenv('DB_NAME', 'govwatcher'),
            user=os.getenv('DB_USER', 'archive_admin'),
            password=os.getenv('DB_PASSWORD')
        )
        redis_client = RedisClient(
            host=os.getenv('REDIS_HOST', 'redis'),
            port=int(os.getenv('REDIS_PORT', '6379')),
            password=os.getenv('REDIS_PASSWORD')
        )
        logger.info("Database and Redis connections established")
    except Exception as e:
        logger.error(f"Failed to initialize connections: {e}")
        sys.exit(1)
    
    # Initialize components
    storage_manager = StorageManager(config, db)
    crawler_manager = CrawlerManager(config, db, redis_client, storage_manager)
    diff_processor = DiffProcessor(config, db, storage_manager)
    
    return config, db, redis_client, crawler_manager, diff_processor, storage_manager

def run_server(config, db, redis_client, crawler_manager, diff_processor, storage_manager):
    """Run the continuous archiving server process"""
    logger.info("Starting archiving server...")
    
    try:
        while True:
            # Process archive queue
            crawler_manager.process_queue()
            
            # Generate diffs for new snapshots
            diff_processor.process_pending_diffs()
            
            # Sleep to avoid constant CPU usage
            time.sleep(config.QUEUE_PROCESSING_INTERVAL)
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Error in server main loop: {e}")
        raise
    finally:
        logger.info("Server shutting down")
        db.close()
        redis_client.close()

def run_single_task(args, config, db, redis_client, crawler_manager, diff_processor, storage_manager):
    """Run a single task and exit"""
    if args.cmd == 'crawl':
        if args.domain:
            logger.info(f"Running single crawl for domain: {args.domain}")
            archive = Archive.get_by_domain(db, args.domain)
            if archive:
                crawler_manager.crawl_archive(archive)
            else:
                logger.error(f"Domain not found: {args.domain}")
        else:
            logger.error("Domain required for crawl command")
    
    elif args.cmd == 'diff':
        if args.archive_id and args.snapshot1 and args.snapshot2:
            logger.info(f"Generating diff between snapshots {args.snapshot1} and {args.snapshot2}")
            diff_processor.generate_diff(args.archive_id, args.snapshot1, args.snapshot2)
        else:
            logger.error("archive_id, snapshot1, and snapshot2 required for diff command")
    
    elif args.cmd == 'import':
        if args.file:
            logger.info(f"Importing domains from file: {args.file}")
            from utils.importers import import_domains
            import_domains(db, args.file, args.priority_file)
        else:
            logger.error("File required for import command")
    
    db.close()
    redis_client.close()

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='GovWatcher Archiving System')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    # Command subparsers
    subparsers = parser.add_subparsers(dest='cmd', help='Command to run')
    
    # Server command
    server_parser = subparsers.add_parser('server', help='Run the continuous archiving server')
    
    # Crawl command
    crawl_parser = subparsers.add_parser('crawl', help='Crawl a specific domain')
    crawl_parser.add_argument('--domain', type=str, help='Domain to crawl')
    
    # Diff command
    diff_parser = subparsers.add_parser('diff', help='Generate a diff between two snapshots')
    diff_parser.add_argument('--archive-id', type=int, help='Archive ID')
    diff_parser.add_argument('--snapshot1', type=int, help='First snapshot ID')
    diff_parser.add_argument('--snapshot2', type=int, help='Second snapshot ID')
    
    # Import command
    import_parser = subparsers.add_parser('import', help='Import domains from a CSV file')
    import_parser.add_argument('--file', type=str, help='Path to CSV file')
    import_parser.add_argument('--priority-file', type=str, help='Path to priority CSV file')
    
    args = parser.parse_args()
    
    # Set log level
    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    # Initialize components
    config, db, redis_client, crawler_manager, diff_processor, storage_manager = setup()
    
    # Run selected command
    if args.cmd == 'server' or not args.cmd:
        run_server(config, db, redis_client, crawler_manager, diff_processor, storage_manager)
    else:
        run_single_task(args, config, db, redis_client, crawler_manager, diff_processor, storage_manager)

if __name__ == "__main__":
    main() 