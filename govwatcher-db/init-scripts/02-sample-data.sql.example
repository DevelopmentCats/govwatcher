-- GovWatcher Sample Data for Testing

-- Add sample archives (government domains)
INSERT INTO archives (domain, domain_type, agency, organization_name, city, state, priority, enabled)
VALUES 
('whitehouse.gov', 'Federal Executive', 'Executive Office of the President', 'The White House', 'Washington', 'DC', 1, TRUE),
('nasa.gov', 'Federal Executive', 'NASA', 'National Aeronautics and Space Administration', 'Washington', 'DC', 1, TRUE),
('cdc.gov', 'Federal Executive', 'HHS', 'Centers for Disease Control and Prevention', 'Atlanta', 'GA', 1, TRUE),
('irs.gov', 'Federal Executive', 'Department of Treasury', 'Internal Revenue Service', 'Washington', 'DC', 2, TRUE),
('dhs.gov', 'Federal Executive', 'DHS', 'Department of Homeland Security', 'Washington', 'DC', 2, TRUE),
('ca.gov', 'State', NULL, 'State of California', 'Sacramento', 'CA', 2, TRUE),
('ny.gov', 'State', NULL, 'State of New York', 'Albany', 'NY', 2, TRUE),
('chicago.gov', 'Local', NULL, 'City of Chicago', 'Chicago', 'IL', 3, TRUE),
('fairfaxcounty.gov', 'Local', NULL, 'Fairfax County', 'Fairfax', 'VA', 3, TRUE),
('tulsacouncil.gov', 'Local', NULL, 'Tulsa City Council', 'Tulsa', 'OK', 3, TRUE);

-- Add sample tags
INSERT INTO tags (name, description) 
VALUES
('federal', 'Federal government websites'),
('state', 'State government websites'),
('local', 'Local government websites'),
('executive', 'Executive branch websites'),
('health', 'Health-related websites'),
('finance', 'Finance-related websites'),
('high-priority', 'High priority websites');

-- Associate tags with archives
INSERT INTO archive_tags (archive_id, tag_id)
VALUES
(1, 1), (1, 4), (1, 7), -- whitehouse.gov: federal, executive, high-priority
(2, 1), (2, 4), (2, 7), -- nasa.gov: federal, executive, high-priority
(3, 1), (3, 4), (3, 5), (3, 7), -- cdc.gov: federal, executive, health, high-priority
(4, 1), (4, 4), (4, 6), -- irs.gov: federal, executive, finance
(5, 1), (5, 4), -- dhs.gov: federal, executive
(6, 2), -- ca.gov: state
(7, 2), -- ny.gov: state
(8, 3), -- chicago.gov: local
(9, 3), -- fairfaxcounty.gov: local
(10, 3); -- tulsacouncil.gov: local

-- Add some sample users
INSERT INTO users (username, password_hash, email, role, created_at, enabled)
VALUES
('operator', crypt('operator123', gen_salt('bf')), 'operator@govwatcher.org', 'operator', NOW(), TRUE),
('viewer', crypt('viewer123', gen_salt('bf')), 'viewer@govwatcher.org', 'viewer', NOW(), TRUE);

-- Sample archive queue entries
INSERT INTO archive_queue (archive_id, operation, status, priority, scheduled_for)
VALUES
(1, 'initial_capture', 'pending', 1, NOW()),
(2, 'initial_capture', 'pending', 1, NOW()),
(3, 'initial_capture', 'pending', 1, NOW()),
(4, 'initial_capture', 'pending', 2, NOW() + INTERVAL '1 hour'),
(5, 'initial_capture', 'pending', 2, NOW() + INTERVAL '2 hours');

-- Insert a few audit log entries
INSERT INTO audit_log (user_id, action, entity_type, entity_id, details, ip_address)
VALUES
(1, 'create', 'archive', 1, '{"domain": "whitehouse.gov"}', '127.0.0.1'),
(1, 'create', 'archive', 2, '{"domain": "nasa.gov"}', '127.0.0.1'),
(1, 'create', 'tag', 1, '{"name": "federal"}', '127.0.0.1'),
(1, 'update', 'archive', 3, '{"priority": 1, "old_priority": 2}', '127.0.0.1');

-- Note: We're not adding sample snapshots or diffs because those would be created
-- by the archive system during actual crawling operations, and would need real file paths. 