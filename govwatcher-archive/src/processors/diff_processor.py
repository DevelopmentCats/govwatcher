import logging
import json
import os
import tempfile
from datetime import datetime
from difflib import SequenceMatcher
from models.snapshot import Snapshot
from models.archive import Archive

logger = logging.getLogger('govwatcher-archive.processors.diff')

class DiffProcessor:
    """Processes diffs between snapshots"""
    
    def __init__(self, config, db, storage_manager):
        self.config = config
        self.db = db
        self.storage = storage_manager
    
    def process_pending_diffs(self):
        """Process diffs that are in the queue"""
        # Find pending diff jobs
        query = """
            SELECT * FROM archive_queue 
            WHERE operation = 'diff' AND status = 'pending'
            ORDER BY priority ASC, scheduled_for ASC
            LIMIT 5
        """
        jobs = self.db.query_all(query)
        
        for job in jobs:
            # Mark job as in progress
            self.db.update('archive_queue', 
                          {'status': 'in_progress', 'started_at': datetime.now()}, 
                          'id = %(id)s', 
                          {'id': job['id']})
            
            try:
                # Get the latest snapshots for this archive
                query = """
                    SELECT old.id as old_id, new.id as new_id
                    FROM snapshots new
                    JOIN snapshots old ON old.archive_id = new.archive_id
                    WHERE new.archive_id = %s
                    ORDER BY new.capture_timestamp DESC
                    LIMIT 2
                """
                snapshots = self.db.query_one(query, (job['archive_id'],))
                
                if snapshots and snapshots['old_id'] != snapshots['new_id']:
                    # Generate diff between the two snapshots
                    self.generate_diff(job['archive_id'], snapshots['old_id'], snapshots['new_id'])
                
                # Mark job as completed
                self.db.update('archive_queue', 
                              {'status': 'completed', 'completed_at': datetime.now()}, 
                              'id = %(id)s', 
                              {'id': job['id']})
                              
            except Exception as e:
                logger.exception(f"Error processing diff job {job['id']}: {str(e)}")
                # Mark job as failed
                self.db.update('archive_queue', 
                              {'status': 'failed', 'error_message': str(e)}, 
                              'id = %(id)s', 
                              {'id': job['id']})
    
    def generate_diff(self, archive_id, old_snapshot_id, new_snapshot_id):
        """Generate a diff between two snapshots"""
        logger.info(f"Generating diff between snapshots {old_snapshot_id} and {new_snapshot_id}")
        
        # Get the snapshots
        old_snapshot = Snapshot.get_by_id(self.db, old_snapshot_id)
        new_snapshot = Snapshot.get_by_id(self.db, new_snapshot_id)
        
        if not old_snapshot or not new_snapshot:
            logger.error(f"Couldn't find snapshots to diff: {old_snapshot_id}, {new_snapshot_id}")
            return None
        
        # Check if diff already exists
        diff_exists = self._check_diff_exists(old_snapshot_id, new_snapshot_id)
        if diff_exists:
            logger.info(f"Diff already exists between {old_snapshot_id} and {new_snapshot_id}")
            return diff_exists
        
        # Get content for both snapshots
        old_content = self._get_snapshot_content(old_snapshot)
        new_content = self._get_snapshot_content(new_snapshot)
        
        if not old_content or not new_content:
            logger.error("Failed to get content for snapshots")
            return None
        
        # Generate the diff
        diff_data = self._generate_text_diff(old_content, new_content)
        
        # Store the diff
        diff_path = self.storage.store_diff(archive_id, old_snapshot_id, new_snapshot_id, diff_data)
        
        # Calculate diff statistics
        stats = self._calculate_diff_stats(diff_data)
        
        # Determine significance
        significance = self._determine_significance(stats)
        
        # Insert diff into database
        diff_id = self.db.insert('diffs', {
            'archive_id': archive_id,
            'old_snapshot_id': old_snapshot_id,
            'new_snapshot_id': new_snapshot_id,
            'diff_timestamp': datetime.now(),
            'diff_path': diff_path,
            'stats': json.dumps(stats),
            'significance': significance
        })
        
        logger.info(f"Created diff {diff_id} with significance {significance}")
        
        # Generate visual diff if enabled
        if self.config.ENABLE_VISUAL_DIFF and old_snapshot.screenshot_path and new_snapshot.screenshot_path:
            try:
                visual_diff_path = self._generate_visual_diff(
                    archive_id, old_snapshot_id, new_snapshot_id,
                    old_snapshot.screenshot_path, new_snapshot.screenshot_path
                )
                
                if visual_diff_path:
                    # Update diff with visual diff path
                    self.db.update('diffs', 
                                  {'visual_diff_path': visual_diff_path}, 
                                  'id = %(id)s', 
                                  {'id': diff_id})
            except Exception as e:
                logger.exception(f"Error generating visual diff: {str(e)}")
        
        return diff_id
    
    def _check_diff_exists(self, old_snapshot_id, new_snapshot_id):
        """Check if a diff already exists between these snapshots"""
        row = self.db.query_one(
            "SELECT id FROM diffs WHERE old_snapshot_id = %s AND new_snapshot_id = %s",
            (old_snapshot_id, new_snapshot_id)
        )
        return row['id'] if row else None
    
    def _get_snapshot_content(self, snapshot):
        """Get the content for a snapshot, preferring HTML"""
        if snapshot.html_path and os.path.exists(snapshot.html_path):
            with open(snapshot.html_path, 'r', encoding='utf-8') as f:
                return f.read()
        elif snapshot.text_path and os.path.exists(snapshot.text_path):
            with open(snapshot.text_path, 'r', encoding='utf-8') as f:
                return f.read()
        return None
    
    def _generate_text_diff(self, old_content, new_content):
        """Generate a text-based diff using difflib"""
        # Split content into lines
        old_lines = old_content.splitlines()
        new_lines = new_content.splitlines()
        
        # Use SequenceMatcher to get opcodes
        matcher = SequenceMatcher(None, old_lines, new_lines)
        opcodes = matcher.get_opcodes()
        
        # Format diff data for react-diff-view
        hunks = []
        hunk_changes = []
        old_start = 1
        new_start = 1
        
        for tag, i1, i2, j1, j2 in opcodes:
            # Skip 'equal' sections if they're too large
            if tag == 'equal' and (i2 - i1) > 10:
                # Only include 3 lines of context
                # Add 3 lines of context at the start
                for i in range(i1, min(i1 + 3, i2)):
                    hunk_changes.append({
                        'type': 'context',
                        'content': old_lines[i],
                        'oldLine': old_start + i - i1,
                        'newLine': new_start + i - i1
                    })
                
                # If we have a current hunk with changes, save it
                if any(c['type'] != 'context' for c in hunk_changes):
                    old_count = i1 + 3 - old_start
                    new_count = j1 + 3 - new_start
                    
                    hunks.append({
                        'content': f"@@ -{old_start},{old_count} +{new_start},{new_count} @@",
                        'oldStart': old_start,
                        'oldLines': old_count,
                        'newStart': new_start,
                        'newLines': new_count,
                        'changes': hunk_changes
                    })
                
                # Reset for next hunk
                hunk_changes = []
                old_start = max(1, i2 - 3)
                new_start = max(1, j2 - 3)
                
                # Add 3 lines of context at the end
                for i in range(max(i1, i2 - 3), i2):
                    hunk_changes.append({
                        'type': 'context',
                        'content': old_lines[i],
                        'oldLine': old_start + i - max(i1, i2 - 3),
                        'newLine': new_start + i - max(i1, i2 - 3)
                    })
                
                continue
            
            # Process changes
            if tag == 'replace':
                # Deletion part
                for i in range(i1, i2):
                    hunk_changes.append({
                        'type': 'delete',
                        'content': '-' + old_lines[i],
                        'oldLine': old_start + i - i1,
                        'newLine': None
                    })
                # Addition part
                for j in range(j1, j2):
                    hunk_changes.append({
                        'type': 'insert',
                        'content': '+' + new_lines[j],
                        'oldLine': None,
                        'newLine': new_start + j - j1
                    })
            elif tag == 'delete':
                for i in range(i1, i2):
                    hunk_changes.append({
                        'type': 'delete',
                        'content': '-' + old_lines[i],
                        'oldLine': old_start + i - i1,
                        'newLine': None
                    })
            elif tag == 'insert':
                for j in range(j1, j2):
                    hunk_changes.append({
                        'type': 'insert',
                        'content': '+' + new_lines[j],
                        'oldLine': None,
                        'newLine': new_start + j - j1
                    })
            elif tag == 'equal':
                for i in range(i1, i2):
                    hunk_changes.append({
                        'type': 'context',
                        'content': ' ' + old_lines[i],
                        'oldLine': old_start + i - i1,
                        'newLine': new_start + j1 + i - i1
                    })
        
        # Add the last hunk if there are changes
        if hunk_changes:
            old_count = i2 - old_start
            new_count = j2 - new_start
            
            hunks.append({
                'content': f"@@ -{old_start},{old_count} +{new_start},{new_count} @@",
                'oldStart': old_start,
                'oldLines': old_count,
                'newStart': new_start,
                'newLines': new_count,
                'changes': hunk_changes
            })
        
        # Convert to JSON-compatible dict
        return {'hunks': hunks}
    
    def _calculate_diff_stats(self, diff_data):
        """Calculate statistics about the diff"""
        additions = 0
        deletions = 0
        changes = 0
        
        for hunk in diff_data.get('hunks', []):
            for change in hunk.get('changes', []):
                if change['type'] == 'insert':
                    additions += 1
                elif change['type'] == 'delete':
                    deletions += 1
                elif change['type'] == 'replace':
                    changes += 1
        
        total_changes = additions + deletions + changes
        return {
            'additions': additions,
            'deletions': deletions, 
            'changes': changes,
            'total': total_changes
        }
    
    def _determine_significance(self, stats):
        """Determine the significance of changes based on stats"""
        total_changes = stats['total']
        
        if total_changes < self.config.DIFF_SIZE_THRESHOLD:
            return 1  # Minor
        elif total_changes < self.config.DIFF_SIZE_THRESHOLD * 5:
            return 2  # Moderate
        else:
            return 3  # Major
    
    def _generate_visual_diff(self, archive_id, old_snapshot_id, new_snapshot_id, old_screenshot, new_screenshot):
        """Generate a visual diff between two screenshots using OpenCV"""
        try:
            import cv2
            import numpy as np
            
            # Read images
            img1 = cv2.imread(old_screenshot)
            img2 = cv2.imread(new_screenshot)
            
            # Make sure both images are the same size
            if img1.shape != img2.shape:
                # Resize the smaller image to match the larger one
                if img1.shape[0] * img1.shape[1] < img2.shape[0] * img2.shape[1]:
                    img1 = cv2.resize(img1, (img2.shape[1], img2.shape[0]))
                else:
                    img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))
            
            # Convert to grayscale
            gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
            
            # Find the difference
            diff = cv2.absdiff(gray1, gray2)
            
            # Threshold the difference
            _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
            
            # Find contours
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Create mask
            mask = np.zeros_like(thresh)
            
            # Draw contours on the mask
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 100:  # Filter small changes
                    cv2.drawContours(mask, [contour], 0, 255, -1)
            
            # Dilate the mask to make changes more visible
            kernel = np.ones((5, 5), np.uint8)
            mask_dilated = cv2.dilate(mask, kernel, iterations=2)
            
            # Create visual diff
            visual_diff = img2.copy()
            
            # Highlight changes in red
            red_mask = np.zeros_like(visual_diff)
            red_mask[mask_dilated == 255] = [0, 0, 255]  # BGR format
            
            # Blend with original
            alpha = 0.7
            cv2.addWeighted(visual_diff, 1, red_mask, alpha, 0, visual_diff)
            
            # Add rectangles around changes
            contours, _ = cv2.findContours(mask_dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(visual_diff, (x, y), (x + w, y + h), (0, 0, 255), 2)
            
            # Save the visual diff
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            cv2.imwrite(temp_file.name, visual_diff)
            
            # Store in the archive
            visual_diff_path = self.storage.store_visual_diff(
                archive_id, old_snapshot_id, new_snapshot_id, temp_file.name
            )
            
            # Clean up temp file
            os.unlink(temp_file.name)
            
            return visual_diff_path
        except ImportError:
            logger.warning("OpenCV not available, skipping visual diff generation")
            return None
        except Exception as e:
            logger.exception(f"Error generating visual diff: {e}")
            return None
