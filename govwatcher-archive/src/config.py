"""
GovWatcher Archive System Configuration
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration settings for the archive system"""
    
    def __init__(self):
        # Database settings
        self.DB_HOST = os.getenv('DB_HOST', 'db')
        self.DB_PORT = int(os.getenv('DB_PORT', '5432'))
        self.DB_NAME = os.getenv('DB_NAME', 'govwatcher')
        self.DB_USER = os.getenv('DB_USER', 'archive_admin')
        self.DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')
        
        # Redis settings
        self.REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
        self.REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
        self.REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')
        
        # Archive storage settings
        self.STORAGE_PATH = os.getenv('ARCHIVE_DATA_PATH', '/data/archives')
        self.WARC_SUBDIR = 'warc'
        self.SCREENSHOT_SUBDIR = 'screenshots'
        self.HTML_SUBDIR = 'html'
        self.PDF_SUBDIR = 'pdf'
        self.TEXT_SUBDIR = 'text'
        self.DIFF_SUBDIR = 'diffs'
        
        # Crawler settings
        self.CRAWLER_USER_AGENT = os.getenv('CRAWLER_USER_AGENT', 
            'GovWatcher/1.0 (+https://govwatcher.org/bot; bot@govwatcher.org)')
        self.MAX_CRAWL_DEPTH = int(os.getenv('MAX_CRAWL_DEPTH', '3'))
        self.MAX_CRAWL_PAGES = int(os.getenv('MAX_CRAWL_PAGES', '1000'))
        self.CRAWL_TIMEOUT = int(os.getenv('CRAWL_TIMEOUT', '300'))  # seconds
        self.CRAWL_DELAY = float(os.getenv('CRAWL_DELAY', '1.0'))  # seconds between requests
        self.MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
        self.RETRY_DELAY = int(os.getenv('RETRY_DELAY', '60'))  # seconds
        
        # Concurrency settings
        self.MAX_CONCURRENT_CRAWLS = int(os.getenv('MAX_CONCURRENT_CRAWLS', '3'))
        self.QUEUE_PROCESSING_INTERVAL = int(os.getenv('QUEUE_PROCESSING_INTERVAL', '10'))  # seconds
        
        # Queue priority thresholds
        self.HIGH_PRIORITY_THRESHOLD = int(os.getenv('HIGH_PRIORITY_THRESHOLD', '1'))
        self.NORMAL_PRIORITY_THRESHOLD = int(os.getenv('NORMAL_PRIORITY_THRESHOLD', '3'))
        
        # Scheduled check intervals (in seconds)
        self.HIGH_PRIORITY_INTERVAL = int(os.getenv('HIGH_PRIORITY_INTERVAL', str(7 * 24 * 3600)))  # 1 week
        self.NORMAL_PRIORITY_INTERVAL = int(os.getenv('NORMAL_PRIORITY_INTERVAL', str(14 * 24 * 3600)))  # 2 weeks
        self.LOW_PRIORITY_INTERVAL = int(os.getenv('LOW_PRIORITY_INTERVAL', str(30 * 24 * 3600)))  # 1 month
        
        # Diff settings
        self.DIFF_SIMILARITY_THRESHOLD = float(os.getenv('DIFF_SIMILARITY_THRESHOLD', '0.9'))
        self.DIFF_SIZE_THRESHOLD = int(os.getenv('DIFF_SIZE_THRESHOLD', '10'))  # min number of changes to be significant
        
        # Webhook settings
        self.WEBHOOK_API_URL = os.getenv('WEBHOOK_API_URL', 'http://api:3000/webhooks')
        self.WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET', 'webhook_secret')
        
        # Feature flags
        self.ENABLE_SCREENSHOTS = os.getenv('ENABLE_SCREENSHOTS', 'true').lower() == 'true'
        self.ENABLE_PDF = os.getenv('ENABLE_PDF', 'true').lower() == 'true'
        self.ENABLE_TEXT_EXTRACTION = os.getenv('ENABLE_TEXT_EXTRACTION', 'true').lower() == 'true'
        self.ENABLE_VISUAL_DIFF = os.getenv('ENABLE_VISUAL_DIFF', 'true').lower() == 'true'
        self.ENABLE_WEBHOOKS = os.getenv('ENABLE_WEBHOOKS', 'true').lower() == 'true' 