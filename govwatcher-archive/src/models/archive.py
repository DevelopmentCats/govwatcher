import logging
from datetime import datetime

logger = logging.getLogger('govwatcher-archive.models.archive')

class Archive:
    """Represents a monitored website in the system"""
    
    def __init__(self, id=None, domain=None, domain_type=None, agency=None, 
                 organization_name=None, city=None, state=None, 
                 security_contact_email=None, priority=3, created_at=None, 
                 last_checked_at=None, last_changed_at=None, enabled=True):
        self.id = id
        self.domain = domain
        self.domain_type = domain_type
        self.agency = agency
        self.organization_name = organization_name
        self.city = city
        self.state = state
        self.security_contact_email = security_contact_email
        self.priority = priority
        self.created_at = created_at or datetime.now()
        self.last_checked_at = last_checked_at
        self.last_changed_at = last_changed_at
        self.enabled = enabled
    
    @classmethod
    def from_dict(cls, data):
        """Create an Archive instance from a dictionary"""
        return cls(**data)
    
    @classmethod
    def from_row(cls, row):
        """Create an Archive instance from a database row"""
        return cls(**dict(row))
    
    @classmethod
    def get_by_id(cls, db, archive_id):
        """Get an archive by ID"""
        row = db.query_one("SELECT * FROM archives WHERE id = %s", (archive_id,))
        if row:
            return cls.from_row(row)
        return None
    
    @classmethod
    def get_by_domain(cls, db, domain):
        """Get an archive by domain"""
        row = db.query_one("SELECT * FROM archives WHERE domain = %s", (domain,))
        if row:
            return cls.from_row(row)
        return None
    
    @classmethod
    def get_all(cls, db, enabled_only=True, limit=None, offset=None):
        """Get all archives, optionally filtered by enabled status"""
        query = "SELECT * FROM archives"
        params = []
        
        if enabled_only:
            query += " WHERE enabled = TRUE"
        
        query += " ORDER BY priority ASC, last_checked_at ASC NULLS FIRST"
        
        if limit is not None:
            query += f" LIMIT %s"
            params.append(limit)
        
        if offset is not None:
            query += f" OFFSET %s"
            params.append(offset)
        
        rows = db.query_all(query, tuple(params) if params else None)
        return [cls.from_row(row) for row in rows]
    
    @classmethod
    def get_pending(cls, db, max_records=10):
        """Get archives that need to be checked based on priority and last check time"""
        query = """
            SELECT a.* FROM archives a
            LEFT JOIN archive_queue q ON a.id = q.archive_id AND q.status IN ('pending', 'in_progress')
            WHERE a.enabled = TRUE
            AND q.id IS NULL
            ORDER BY a.priority ASC, a.last_checked_at ASC NULLS FIRST
            LIMIT %s
        """
        rows = db.query_all(query, (max_records,))
        return [cls.from_row(row) for row in rows]
    
    def save(self, db):
        """Save the archive to the database"""
        if self.id:
            # Update existing record
            data = {
                'domain': self.domain,
                'domain_type': self.domain_type,
                'agency': self.agency,
                'organization_name': self.organization_name,
                'city': self.city,
                'state': self.state,
                'security_contact_email': self.security_contact_email,
                'priority': self.priority,
                'last_checked_at': self.last_checked_at,
                'last_changed_at': self.last_changed_at,
                'enabled': self.enabled
            }
            db.update('archives', data, 'id = %(id)s', {'id': self.id})
            return self.id
        else:
            # Insert new record
            data = {
                'domain': self.domain,
                'domain_type': self.domain_type,
                'agency': self.agency,
                'organization_name': self.organization_name,
                'city': self.city,
                'state': self.state,
                'security_contact_email': self.security_contact_email,
                'priority': self.priority,
                'created_at': self.created_at,
                'last_checked_at': self.last_checked_at,
                'last_changed_at': self.last_changed_at,
                'enabled': self.enabled
            }
            self.id = db.insert('archives', data)
            return self.id
    
    def update_check_time(self, db):
        """Update the last_checked_at timestamp"""
        self.last_checked_at = datetime.now()
        db.update('archives', 
                  {'last_checked_at': self.last_checked_at}, 
                  'id = %(id)s', 
                  {'id': self.id})
    
    def update_change_time(self, db):
        """Update the last_changed_at timestamp"""
        self.last_changed_at = datetime.now()
        db.update('archives', 
                  {'last_changed_at': self.last_changed_at, 'last_checked_at': self.last_checked_at}, 
                  'id = %(id)s', 
                  {'id': self.id})
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'domain': self.domain,
            'domain_type': self.domain_type,
            'agency': self.agency,
            'organization_name': self.organization_name,
            'city': self.city,
            'state': self.state,
            'security_contact_email': self.security_contact_email,
            'priority': self.priority,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_checked_at': self.last_checked_at.isoformat() if self.last_checked_at else None,
            'last_changed_at': self.last_changed_at.isoformat() if self.last_changed_at else None,
            'enabled': self.enabled
        }
