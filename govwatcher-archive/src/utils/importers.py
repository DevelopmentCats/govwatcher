import csv
import logging
from datetime import datetime
from models.archive import Archive
import os

logger = logging.getLogger('govwatcher-archive.utils.importers')

def import_domains(db, csv_file, priority_csv=None):
    """
    Import domains from a CSV file into the database.
    
    Args:
        db: Database connection
        csv_file: Path to CSV file with domains (CISA .gov dataset)
        priority_csv: Optional path to CSV file with higher priority domains
    
    Returns:
        tuple: (total_imported, updated, created)
    """
    logger.info(f"Importing domains from {csv_file}")
    
    # Set up priority domains if provided
    priority_domains = set()
    if priority_csv and os.path.exists(priority_csv):
        with open(priority_csv, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'domain' in row:
                    priority_domains.add(row['domain'].lower())
        logger.info(f"Loaded {len(priority_domains)} priority domains")
    
    # Import domains from main CSV
    created = 0
    updated = 0
    total = 0
    
    with open(csv_file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            total += 1
            # Map CSV columns to Archive fields
            domain = row.get('domain', '').lower()
            
            if not domain:
                continue
            
            # Check if domain already exists
            existing = Archive.get_by_domain(db, domain)
            
            # Set priority based on whether it's in priority_domains
            priority = 1 if domain in priority_domains else 3
            
            archive_data = {
                'domain': domain,
                'domain_type': row.get('domainType'),
                'agency': row.get('agency') or row.get('federalAgency'),
                'organization_name': row.get('organizationName', ''),
                'city': row.get('city', ''),
                'state': row.get('state', ''),
                'security_contact_email': row.get('securityContact', ''),
                'priority': priority,
                'enabled': True
            }
            
            if existing:
                # Update existing domain
                archive = Archive.from_dict({**archive_data, 'id': existing.id})
                archive.save(db)
                updated += 1
            else:
                # Create new domain
                archive = Archive.from_dict(archive_data)
                archive.save(db)
                created += 1
            
            # Commit every 100 records
            if (created + updated) % 100 == 0:
                logger.info(f"Processed {created + updated} domains...")
    
    logger.info(f"Import complete: {total} total, {created} created, {updated} updated")
    return total, created, updated
