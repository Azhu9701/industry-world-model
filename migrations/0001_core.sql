CREATE TABLE IF NOT EXISTS entities (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    pack text NOT NULL,
    entity_type text NOT NULL,
    entity_key text NOT NULL,
    name text NOT NULL,
    description text,
    status text NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'merged', 'hidden')),
    attributes jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(attributes) = 'object'),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (pack, entity_type, entity_key)
);

CREATE TABLE IF NOT EXISTS entity_aliases (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id uuid NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    alias text NOT NULL,
    normalized_alias text NOT NULL,
    locale text,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (entity_id, normalized_alias)
);

CREATE INDEX IF NOT EXISTS entity_aliases_lookup_idx ON entity_aliases (normalized_alias);

CREATE TABLE IF NOT EXISTS sources (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    url text NOT NULL UNIQUE CHECK (url ~ '^https?://'),
    title text NOT NULL,
    publisher text,
    source_type text NOT NULL DEFAULT 'web',
    published_at timestamptz,
    accessed_at timestamptz NOT NULL DEFAULT now(),
    license text,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(metadata) = 'object'),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS claims (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_id uuid NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    predicate text NOT NULL,
    value jsonb NOT NULL,
    unit text,
    confidence numeric(4,3) CHECK (confidence BETWEEN 0 AND 1),
    status text NOT NULL DEFAULT 'proposed' CHECK (status IN ('proposed', 'verified', 'disputed', 'rejected', 'superseded')),
    valid_from date,
    valid_to date,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CHECK (valid_to IS NULL OR valid_from IS NULL OR valid_to >= valid_from)
);

CREATE INDEX IF NOT EXISTS claims_subject_predicate_idx ON claims (subject_id, predicate);

CREATE TABLE IF NOT EXISTS relations (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_id uuid NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    predicate text NOT NULL,
    object_id uuid NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    status text NOT NULL DEFAULT 'proposed' CHECK (status IN ('proposed', 'verified', 'disputed', 'rejected', 'superseded')),
    valid_from date,
    valid_to date,
    attributes jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(attributes) = 'object'),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CHECK (subject_id <> object_id),
    CHECK (valid_to IS NULL OR valid_from IS NULL OR valid_to >= valid_from),
    UNIQUE NULLS NOT DISTINCT (subject_id, predicate, object_id, valid_from)
);

CREATE INDEX IF NOT EXISTS relations_object_idx ON relations (object_id, predicate);

CREATE TABLE IF NOT EXISTS events (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    pack text NOT NULL,
    event_type text NOT NULL,
    event_key text NOT NULL,
    title text NOT NULL,
    summary text,
    occurred_on date,
    occurred_end date,
    date_precision text NOT NULL DEFAULT 'day' CHECK (date_precision IN ('day', 'month', 'year', 'unknown')),
    classification text NOT NULL DEFAULT 'NEW_EVENT' CHECK (classification IN ('NEW_EVENT', 'FOLLOW_UP', 'ENRICHMENT')),
    status text NOT NULL DEFAULT 'proposed' CHECK (status IN ('proposed', 'verified', 'disputed', 'rejected', 'hidden')),
    attributes jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(attributes) = 'object'),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CHECK (occurred_end IS NULL OR occurred_on IS NULL OR occurred_end >= occurred_on),
    UNIQUE (pack, event_key)
);

CREATE INDEX IF NOT EXISTS events_timeline_idx ON events (occurred_on DESC, id);

CREATE TABLE IF NOT EXISTS event_entities (
    event_id uuid NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    entity_id uuid NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    role text NOT NULL DEFAULT 'participant',
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (event_id, entity_id, role)
);

CREATE TABLE IF NOT EXISTS media_assets (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id uuid REFERENCES entities(id) ON DELETE SET NULL,
    source_id uuid REFERENCES sources(id) ON DELETE SET NULL,
    media_type text NOT NULL CHECK (media_type IN ('image', 'video', 'audio', 'document')),
    url text NOT NULL CHECK (url ~ '^https?://'),
    sha256 text,
    alt_text text,
    width integer CHECK (width IS NULL OR width > 0),
    height integer CHECK (height IS NULL OR height > 0),
    status text NOT NULL DEFAULT 'proposed' CHECK (status IN ('proposed', 'verified', 'rejected', 'withdrawn')),
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(metadata) = 'object'),
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (url)
);

CREATE TABLE IF NOT EXISTS evidences (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id uuid NOT NULL REFERENCES sources(id) ON DELETE RESTRICT,
    claim_id uuid REFERENCES claims(id) ON DELETE CASCADE,
    relation_id uuid REFERENCES relations(id) ON DELETE CASCADE,
    event_id uuid REFERENCES events(id) ON DELETE CASCADE,
    media_asset_id uuid REFERENCES media_assets(id) ON DELETE CASCADE,
    source_locator text,
    excerpt text,
    excerpt_sha256 text,
    captured_at timestamptz NOT NULL DEFAULT now(),
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK (num_nonnulls(claim_id, relation_id, event_id, media_asset_id) = 1)
);

CREATE INDEX IF NOT EXISTS evidences_source_idx ON evidences (source_id);
CREATE INDEX IF NOT EXISTS evidences_claim_idx ON evidences (claim_id) WHERE claim_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS evidences_relation_idx ON evidences (relation_id) WHERE relation_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS evidences_event_idx ON evidences (event_id) WHERE event_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS ingest_jobs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    pack text NOT NULL,
    input_uri text,
    status text NOT NULL DEFAULT 'queued' CHECK (status IN ('queued', 'running', 'review', 'completed', 'failed', 'cancelled')),
    idempotency_key text NOT NULL UNIQUE,
    stats jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(stats) = 'object'),
    error text,
    created_at timestamptz NOT NULL DEFAULT now(),
    started_at timestamptz,
    finished_at timestamptz
);

CREATE TABLE IF NOT EXISTS review_tasks (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    target_kind text NOT NULL CHECK (target_kind IN ('entity', 'claim', 'relation', 'event', 'media_asset', 'ingest_job')),
    target_id uuid NOT NULL,
    reason text NOT NULL,
    status text NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'approved', 'rejected', 'changes_requested')),
    assigned_to text,
    decision_note text,
    created_at timestamptz NOT NULL DEFAULT now(),
    decided_at timestamptz
);

CREATE INDEX IF NOT EXISTS review_tasks_queue_idx ON review_tasks (status, created_at);

CREATE TABLE IF NOT EXISTS change_logs (
    id bigserial PRIMARY KEY,
    actor text NOT NULL,
    action text NOT NULL,
    target_kind text NOT NULL,
    target_id uuid,
    before_state jsonb,
    after_state jsonb,
    reason text,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS change_logs_target_idx ON change_logs (target_kind, target_id, created_at DESC);
