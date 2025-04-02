import os
import logging
import shutil
import hashlib
from datetime import datetime
import json

logger = logging.getLogger('govwatcher-archive.storage.manager')

class StorageManager:
    """Manages file storage for the archiving system"""
    
    def __init__(self, config, db):
        self.config = config
        self.db = db
        self.base_path = config.STORAGE_PATH
        
        # Ensure storage directories exist
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure all necessary directories exist"""
        # Base directory
        os.makedirs(self.base_path, exist_ok=True)
        
        # Subdirectories (will be created on demand)
    
    def get_archive_path(self, archive_id):
        """Get the path for a specific archive"""
        return os.path.join(self.base_path, str(archive_id))
    
    def get_snapshot_path(self, archive_id, snapshot_id):
        """Get the path for a specific snapshot"""
        return os.path.join(self.get_archive_path(archive_id), 'snapshots', str(snapshot_id))
    
    def get_diff_path(self, archive_id, old_snapshot_id, new_snapshot_id):
        """Get the path for a specific diff"""
        diff_id = f"{old_snapshot_id}_{new_snapshot_id}"
        return os.path.join(self.get_archive_path(archive_id), 'diffs', diff_id)
    
    def store_warc(self, archive_id, snapshot_id, warc_file):
        """Store a WARC file"""
        snapshot_dir = self.get_snapshot_path(archive_id, snapshot_id)
        os.makedirs(snapshot_dir, exist_ok=True)
        
        target_path = os.path.join(snapshot_dir, 'original.warc')
        
        # Copy the file (or move if it's a temporary file)
        if os.path.isfile(warc_file):
            shutil.copy2(warc_file, target_path)
        
        return target_path
    
    def store_screenshot(self, archive_id, snapshot_id, screenshot_file):
        """Store a screenshot"""
        snapshot_dir = self.get_snapshot_path(archive_id, snapshot_id)
        os.makedirs(snapshot_dir, exist_ok=True)
        
        target_path = os.path.join(snapshot_dir, 'screenshot.png')
        
        # Copy the file
        if os.path.isfile(screenshot_file):
            shutil.copy2(screenshot_file, target_path)
        
        return target_path
    
    def store_html(self, archive_id, snapshot_id, html_content):
        """Store HTML content"""
        snapshot_dir = self.get_snapshot_path(archive_id, snapshot_id)
        os.makedirs(snapshot_dir, exist_ok=True)
        
        target_path = os.path.join(snapshot_dir, 'content.html')
        
        # Write content to file
        if isinstance(html_content, str):
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
        elif isinstance(html_content, bytes):
            with open(target_path, 'wb') as f:
                f.write(html_content)
        
        # Calculate hash
        hasher = hashlib.sha256()
        if isinstance(html_content, str):
            hasher.update(html_content.encode('utf-8'))
        else:
            hasher.update(html_content)
        content_hash = hasher.hexdigest()
        
        return target_path, content_hash
    
    def store_text(self, archive_id, snapshot_id, text_content):
        """Store extracted text content"""
        snapshot_dir = self.get_snapshot_path(archive_id, snapshot_id)
        os.makedirs(snapshot_dir, exist_ok=True)
        
        target_path = os.path.join(snapshot_dir, 'content.txt')
        
        # Write content to file
        if isinstance(text_content, str):
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(text_content)
        
        return target_path
    
    def store_pdf(self, archive_id, snapshot_id, pdf_file):
        """Store a PDF version"""
        snapshot_dir = self.get_snapshot_path(archive_id, snapshot_id)
        os.makedirs(snapshot_dir, exist_ok=True)
        
        target_path = os.path.join(snapshot_dir, 'content.pdf')
        
        # Copy the file
        if os.path.isfile(pdf_file):
            shutil.copy2(pdf_file, target_path)
        
        return target_path
    
    def store_diff(self, archive_id, old_snapshot_id, new_snapshot_id, diff_data):
        """Store diff data"""
        diff_dir = self.get_diff_path(archive_id, old_snapshot_id, new_snapshot_id)
        os.makedirs(diff_dir, exist_ok=True)
        
        target_path = os.path.join(diff_dir, 'diff.json')
        
        # Write diff data to file
        with open(target_path, 'w', encoding='utf-8') as f:
            json.dump(diff_data, f)
        
        return target_path
    
    def store_visual_diff(self, archive_id, old_snapshot_id, new_snapshot_id, visual_diff_file):
        """Store a visual diff image"""
        diff_dir = self.get_diff_path(archive_id, old_snapshot_id, new_snapshot_id)
        os.makedirs(diff_dir, exist_ok=True)
        
        target_path = os.path.join(diff_dir, 'visual-diff.png')
        
        # Copy the file
        if os.path.isfile(visual_diff_file):
            shutil.copy2(visual_diff_file, target_path)
        
        return target_path
    
    def get_file_size(self, file_path):
        """Get the size of a file in bytes"""
        if os.path.isfile(file_path):
            return os.path.getsize(file_path)
        return 0
