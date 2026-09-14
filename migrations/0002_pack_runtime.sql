CREATE INDEX IF NOT EXISTS entities_pack_type_name_idx
    ON entities (pack, entity_type, name);

CREATE INDEX IF NOT EXISTS events_pack_timeline_idx
    ON events (pack, occurred_on DESC, created_at DESC);

CREATE INDEX IF NOT EXISTS ingest_jobs_pack_status_created_idx
    ON ingest_jobs (pack, status, created_at DESC);

CREATE INDEX IF NOT EXISTS review_tasks_ingest_queue_idx
    ON review_tasks (target_kind, status, created_at DESC)
    WHERE target_kind = 'ingest_job';
