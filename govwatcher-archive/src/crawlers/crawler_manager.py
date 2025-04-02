import logging
import time
from datetime import datetime, timedelta
from models.archive import Archive
from models.snapshot import Snapshot

logger = logging.getLogger('govwatcher-archive.crawlers.manager')

class CrawlerManager:
    """Manages the crawling process and scheduling"""
    
    def __init__(self, config, db, redis_client, storage_manager):
        self.config = config
        self.db = db
        self.redis = redis_client
        self.storage = storage_manager
        self.active_crawls = set()
        self.from_imports = __import__('crawlers.webpage_crawler', fromlist=['WebpageCrawler']).WebpageCrawler
    
    def process_queue(self):
        """Process the archive queue to find sites that need crawling"""
        # Check if we have capacity for more crawls
        if len(self.active_crawls) >= self.config.MAX_CONCURRENT_CRAWLS:
            logger.debug(f"Already at max concurrent crawls: {len(self.active_crawls)}")
            return
        
        available_slots = self.config.MAX_CONCURRENT_CRAWLS - len(self.active_crawls)
        
        # Get archives that need checking based on priority and last check time
        pending_archives = Archive.get_pending(self.db, max_records=available_slots)
        
        if not pending_archives:
            return
        
        logger.info(f"Found {len(pending_archives)} archives to process")
        
        # Schedule each archive for crawling
        for archive in pending_archives:
            self._schedule_archive(archive)
    
    def _schedule_archive(self, archive):
        """Schedule an archive for crawling"""
        logger.info(f"Scheduling crawl for {archive.domain} (ID: {archive.id})")
        
        # Determine priority based on archive priority
        priority = 1 if archive.priority <= self.config.HIGH_PRIORITY_THRESHOLD else \
                   3 if archive.priority <= self.config.NORMAL_PRIORITY_THRESHOLD else 5
        
        # Add to queue
        job_data = {'id': archive.id, 'domain': archive.domain}
        queue_name = 'archive:crawl'
        
        job_id = self.redis.enqueue_job(queue_name, job_data, priority=priority)
        logger.debug(f"Added job {job_id} to queue {queue_name}")
        
        # Add to database queue
        self.db.insert('archive_queue', {
            'archive_id': archive.id,
            'operation': 'crawl',
            'status': 'pending',
            'priority': priority,
            'scheduled_for': datetime.now()
        })
    
    def crawl_archive(self, archive):
        """Crawl a specific archive"""
        if archive.id in self.active_crawls:
            logger.warning(f"Archive {archive.id} is already being crawled")
            return False
        
        logger.info(f"Starting crawl for {archive.domain} (ID: {archive.id})")
        
        try:
            self.active_crawls.add(archive.id)
            
            # Create crawler
            crawler = self.from_imports(self.config)
            
            # Perform crawl
            result = crawler.crawl(archive.domain)
            
            if result.success:
                # Update archive last checked time
                archive.update_check_time(self.db)
                
                # Create snapshot
                snapshot = Snapshot(
                    archive_id=archive.id,
                    capture_timestamp=datetime.now(),
                    warc_path=result.warc_path,
                    screenshot_path=result.screenshot_path,
                    html_path=result.html_path,
                    text_path=result.text_path,
                    pdf_path=result.pdf_path,
                    content_hash=result.content_hash,
                    status=result.status_code,
                    size_bytes=result.size_bytes,
                    metadata=result.metadata
                )
                
                snapshot_id = snapshot.save(self.db)
                logger.info(f"Created snapshot {snapshot_id} for archive {archive.id}")
                
                # Check for changes
                self._process_changes(archive, snapshot)
                
                return True
            else:
                logger.error(f"Crawl failed for {archive.domain}: {result.error}")
                return False
                
        except Exception as e:
            logger.exception(f"Error crawling {archive.domain}: {str(e)}")
            return False
        finally:
            self.active_crawls.remove(archive.id)
    
    def _process_changes(self, archive, new_snapshot):
        """Check for changes between the new snapshot and the previous one"""
        # Get the previous snapshot
        previous_snapshot = Snapshot.get_latest_for_archive(self.db, archive.id)
        
        # If this is the first snapshot, no changes to detect
        if not previous_snapshot or previous_snapshot.id == new_snapshot.id:
            return
        
        # Compare content hashes
        if previous_snapshot.content_hash == new_snapshot.content_hash:
            logger.info(f"No changes detected for {archive.domain}")
            return
        
        # Content has changed, update last_changed_at
        archive.update_change_time(self.db)
        
        # Queue diff generation
        job_data = {
            'archive_id': archive.id,
            'old_snapshot_id': previous_snapshot.id,
            'new_snapshot_id': new_snapshot.id
        }
        
        # Add to Redis queue
        queue_name = 'archive:diff'
        job_id = self.redis.enqueue_job(queue_name, job_data, priority=3)
        logger.debug(f"Added diff job {job_id} to queue {queue_name}")
        
        # Add to database queue
        self.db.insert('archive_queue', {
            'archive_id': archive.id,
            'operation': 'diff',
            'status': 'pending',
            'priority': 3,
            'scheduled_for': datetime.now()
        })
        
        logger.info(f"Changes detected for {archive.domain}, queued diff generation")
