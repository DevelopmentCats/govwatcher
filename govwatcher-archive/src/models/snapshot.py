import logging
from datetime import datetime
import hashlib
import json

logger = logging.getLogger('govwatcher-archive.models.snapshot')

class Snapshot:
    """Represents a captured snapshot of a website"""
    
    def __init__(self, id=None, archive_id=None, capture_timestamp=None, warc_path=None, 
                 screenshot_path=None, html_path=None, text_path=None, pdf_path=None, 
                 content_hash=None, status=None, size_bytes=None, error_message=None, 
                 metadata=None):
        self.id = id
        self.archive_id = archive_id
        self.capture_timestamp = capture_timestamp or datetime.now()
        self.warc_path = warc_path
        self.screenshot_path = screenshot_path
        self.html_path = html_path
        self.text_path = text_path
        self.pdf_path = pdf_path
        self.content_hash = content_hash
        self.status = status
        self.size_bytes = size_bytes
        self.error_message = error_message
        self.metadata = metadata or {}
    
    @classmethod
    def from_dict(cls, data):
        """Create a Snapshot instance from a dictionary"""
        if isinstance(data.get('metadata'), str):
            data['metadata'] = json.loads(data['metadata'])
        return cls(**data)
    
    @classmethod
    def from_row(cls, row):
        """Create a Snapshot instance from a database row"""
        data = dict(row)
        if isinstance(data.get('metadata'), str):
            data['metadata'] = json.loads(data['metadata'])
        return cls(**data)
    
    @classmethod
    def get_by_id(cls, db, snapshot_id):
        """Get a snapshot by ID"""
        row = db.query_one("SELECT * FROM snapshots WHERE id = %s", (snapshot_id,))
        if row:
            return cls.from_row(row)
        return None
    
    @classmethod
    def get_latest_for_archive(cls, db, archive_id):
        """Get the latest snapshot for an archive"""
        row = db.query_one(
            "SELECT * FROM snapshots WHERE archive_id = %s ORDER BY capture_timestamp DESC LIMIT 1", 
            (archive_id,)
        )
        if row:
            return cls.from_row(row)
        return None
    
    @classmethod
    def get_for_archive(cls, db, archive_id, limit=10, offset=0):
        """Get snapshots for an archive with pagination"""
        rows = db.query_all(
            "SELECT * FROM snapshots WHERE archive_id = %s ORDER BY capture_timestamp DESC LIMIT %s OFFSET %s", 
            (archive_id, limit, offset)
        )
        return [cls.from_row(row) for row in rows]
    
    def save(self, db):
        """Save the snapshot to the database"""
        if self.id:
            # Update existing record
            data = {
                'archive_id': self.archive_id,
                'capture_timestamp': self.capture_timestamp,
                'warc_path': self.warc_path,
                'screenshot_path': self.screenshot_path,
                'html_path': self.html_path,
                'text_path': self.text_path,
                'pdf_path': self.pdf_path,
                'content_hash': self.content_hash,
                'status': self.status,
                'size_bytes': self.size_bytes,
                'error_message': self.error_message,
                'metadata': json.dumps(self.metadata) if self.metadata else None
            }
            db.update('snapshots', data, 'id = %(id)s', {'id': self.id})
            return self.id
        else:
            # Insert new record
            data = {
                'archive_id': self.archive_id,
                'capture_timestamp': self.capture_timestamp,
                'warc_path': self.warc_path,
                'screenshot_path': self.screenshot_path,
                'html_path': self.html_path,
                'text_path': self.text_path,
                'pdf_path': self.pdf_path,
                'content_hash': self.content_hash,
                'status': self.status,
                'size_bytes': self.size_bytes,
                'error_message': self.error_message,
                'metadata': json.dumps(self.metadata) if self.metadata else None
            }
            self.id = db.insert('snapshots', data)
            return self.id
    
    def calculate_content_hash(self, content):
        """Calculate a hash of the content"""
        hasher = hashlib.sha256()
        if isinstance(content, str):
            hasher.update(content.encode('utf-8'))
        else:
            hasher.update(content)
        self.content_hash = hasher.hexdigest()
        return self.content_hash
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'archive_id': self.archive_id,
            'capture_timestamp': self.capture_timestamp.isoformat() if self.capture_timestamp else None,
            'warc_path': self.warc_path,
            'screenshot_path': self.screenshot_path,
            'html_path': self.html_path,
            'text_path': self.text_path,
            'pdf_path': self.pdf_path,
            'content_hash': self.content_hash,
            'status': self.status,
            'size_bytes': self.size_bytes,
            'error_message': self.error_message,
            'metadata': self.metadata
        }
