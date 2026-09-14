INSERT INTO entities (id, pack, entity_type, entity_key, name, description)
VALUES
    ('00000000-0000-4000-8000-000000000001', 'example', 'company', 'acme-robotics', 'Acme Robotics', 'Fictional company for local development.'),
    ('00000000-0000-4000-8000-000000000002', 'example', 'product', 'atlas-mini', 'Atlas Mini', 'Fictional product for local development.')
ON CONFLICT (id) DO NOTHING;

INSERT INTO sources (id, url, title, publisher, metadata)
VALUES (
    '00000000-0000-4000-8000-000000000003',
    'https://example.com/',
    'Example Domain',
    'IANA',
    '{"synthetic_seed": true}'::jsonb
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO claims (id, subject_id, predicate, value, status)
VALUES (
    '00000000-0000-4000-8000-000000000004',
    '00000000-0000-4000-8000-000000000001',
    'website',
    '"https://example.com/"'::jsonb,
    'proposed'
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO relations (id, subject_id, predicate, object_id, status)
VALUES (
    '00000000-0000-4000-8000-000000000005',
    '00000000-0000-4000-8000-000000000001',
    'produces',
    '00000000-0000-4000-8000-000000000002',
    'proposed'
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO events (id, pack, event_type, event_key, title, occurred_on, classification, status)
VALUES (
    '00000000-0000-4000-8000-000000000006',
    'example',
    'product_release',
    'example-atlas-mini-release',
    'Atlas Mini release (synthetic)',
    '2026-01-01',
    'NEW_EVENT',
    'proposed'
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO event_entities (event_id, entity_id, role)
VALUES
    ('00000000-0000-4000-8000-000000000006', '00000000-0000-4000-8000-000000000001', 'announcer'),
    ('00000000-0000-4000-8000-000000000006', '00000000-0000-4000-8000-000000000002', 'subject')
ON CONFLICT DO NOTHING;

INSERT INTO evidences (id, source_id, claim_id, relation_id, event_id, source_locator, excerpt)
VALUES
    ('00000000-0000-4000-8000-000000000007', '00000000-0000-4000-8000-000000000003', '00000000-0000-4000-8000-000000000004', NULL, NULL, 'page', 'Synthetic evidence for schema demonstration only.'),
    ('00000000-0000-4000-8000-000000000008', '00000000-0000-4000-8000-000000000003', NULL, '00000000-0000-4000-8000-000000000005', NULL, 'page', 'Synthetic evidence for schema demonstration only.'),
    ('00000000-0000-4000-8000-000000000009', '00000000-0000-4000-8000-000000000003', NULL, NULL, '00000000-0000-4000-8000-000000000006', 'page', 'Synthetic evidence for schema demonstration only.')
ON CONFLICT (id) DO NOTHING;
