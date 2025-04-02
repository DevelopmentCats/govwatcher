"""
Client for interacting with ArchiveBox.
"""
import os
import subprocess
import json
import logging
import shutil
from urllib.parse import urlparse

logger = logging.getLogger('govwatcher-archive.archivebox')

class ArchiveBoxClient:
    """Client for interacting with ArchiveBox"""
    
    def __init__(self, config):
        """Initialize the ArchiveBox client"""
        self.config = config
        self.binary = config.ARCHIVEBOX_BINARY
        self.data_dir = config.ARCHIVEBOX_DATA_DIR
        
        # Ensure ArchiveBox data dir exists
        if not os.path.exists(self.data_dir):
            self._initialize_archivebox()
    
    def _initialize_archivebox(self):
        """Initialize ArchiveBox data directory"""
        logger.info(f"Initializing ArchiveBox data directory: {self.data_dir}")
        os.makedirs(self.data_dir, exist_ok=True)
        
        cmd = [self.binary, 'init', '--setup']
        try:
            subprocess.run(cmd, cwd=self.data_dir, check=True)
            logger.info("ArchiveBox initialized successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to initialize ArchiveBox: {e}")
            raise
    
    def add_url(self, url, tag=None, depth=1):
        """Add a URL to ArchiveBox"""
        logger.info(f"Adding URL to ArchiveBox: {url}")
        
        cmd = [self.binary, 'add', url, '--depth', str(depth)]
        
        if tag:
            cmd.extend(['--tag', tag])
        
        try:
            result = subprocess.run(cmd, cwd=self.data_dir, check=True, 
                                  capture_output=True, text=True)
            logger.debug(f"ArchiveBox add output: {result.stdout}")
            return self._parse_add_output(result.stdout, url)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to add URL to ArchiveBox: {e}")
            logger.debug(f"Error output: {e.stderr}")
            return None
    
    def _parse_add_output(self, output, url):
        """Parse the output of the add command to get the snapshot directory"""
        # Try to parse the ID of the created snapshot
        domain = urlparse(url).netloc
        
        # ArchiveBox typically creates a subdirectory based on the URL
        # We'll try to find it in the list of snapshots
        snapshots = self.list_snapshots()
        
        # Find the most recent snapshot for this URL
        matching_snapshots = [s for s in snapshots if s['url'] == url]
        if matching_snapshots:
            # Sort by timestamp, most recent first
            matching_snapshots.sort(key=lambda x: x['timestamp'], reverse=True)
            return matching_snapshots[0]
        
        return None
    
    def list_snapshots(self, filter_domain=None, filter_tag=None, limit=100):
        """List snapshots in ArchiveBox"""
        cmd = [self.binary, 'list', '--json']
        
        if filter_domain:
            cmd.extend(['--filter-domain', filter_domain])
        
        if filter_tag:
            cmd.extend(['--filter-tag', filter_tag])
        
        cmd.extend(['--limit', str(limit)])
        
        try:
            result = subprocess.run(cmd, cwd=self.data_dir, check=True, 
                                  capture_output=True, text=True)
            snapshots = json.loads(result.stdout)
            return snapshots
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to list ArchiveBox snapshots: {e}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse ArchiveBox output: {e}")
            return []
    
    def get_snapshot(self, snapshot_id):
        """Get details for a specific snapshot"""
        cmd = [self.binary, 'data', snapshot_id, '--json']
        
        try:
            result = subprocess.run(cmd, cwd=self.data_dir, check=True, 
                                  capture_output=True, text=True)
            snapshot = json.loads(result.stdout)
            return snapshot
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get ArchiveBox snapshot {snapshot_id}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse ArchiveBox output: {e}")
            return None
    
    def extract_files(self, snapshot_id, target_dir):
        """Extract files from an ArchiveBox snapshot to a target directory"""
        snapshot_dir = os.path.join(self.data_dir, 'archive', snapshot_id)
        
        if not os.path.exists(snapshot_dir):
            logger.error(f"Snapshot directory not found: {snapshot_dir}")
            return None
        
        os.makedirs(target_dir, exist_ok=True)
        
        # Copy the main files
        files_to_copy = {
            'warc': ('archive.warc.gz', 'original.warc'),
            'pdf': ('output.pdf', 'content.pdf'),
            'screenshot': ('screenshot.png', 'screenshot.png'),
            'html': ('index.html', 'content.html')
        }
        
        copied_files = {}
        
        for file_type, (src_name, dst_name) in files_to_copy.items():
            src_path = os.path.join(snapshot_dir, src_name)
            if os.path.exists(src_path):
                dst_path = os.path.join(target_dir, dst_name)
                shutil.copy2(src_path, dst_path)
                copied_files[file_type] = dst_path
            else:
                logger.debug(f"File not found in snapshot: {src_name}")
        
        # Extract text content if available
        if 'html' in copied_files:
            try:
                from bs4 import BeautifulSoup
                with open(copied_files['html'], 'r', encoding='utf-8') as f:
                    soup = BeautifulSoup(f.read(), 'html.parser')
                    text = soup.get_text(separator='\n', strip=True)
                    
                    text_path = os.path.join(target_dir, 'content.txt')
                    with open(text_path, 'w', encoding='utf-8') as f:
                        f.write(text)
                    
                    copied_files['text'] = text_path
            except Exception as e:
                logger.warning(f"Failed to extract text from HTML: {e}")
        
        return copied_files
