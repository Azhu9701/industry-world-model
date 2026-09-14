use axum::{
    Json, Router,
    extract::{Path, Query, State},
    http::{HeaderMap, StatusCode},
    response::{IntoResponse, Response},
    routing::{get, post},
};
use serde::{Deserialize, Serialize};
use serde_json::{Value, json};
use sqlx::{PgPool, Row};
use std::{
    collections::{BTreeMap, HashSet},
    env, fs,
    net::SocketAddr,
    path::{Path as FsPath, PathBuf},
    time::{SystemTime, UNIX_EPOCH},
};
use tower_http::cors::CorsLayer;

#[derive(Clone)]
struct AppState {
    pool: PgPool,
    packs_dir: PathBuf,
    default_pack: String,
    writes_enabled: bool,
    write_key: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct DomainPack {
    name: String,
    title: String,
    version: String,
    entities: BTreeMap<String, EntityDefinition>,
    #[serde(default)]
    claims: Vec<String>,
    #[serde(default)]
    relations: Vec<RelationRule>,
    #[serde(default)]
    events: Vec<String>,
    #[serde(default)]
    event_relations: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct EntityDefinition {
    #[serde(default)]
    label: String,
    #[serde(default)]
    fields: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct RelationRule {
    subject: String,
    predicate: String,
    object: String,
}

#[derive(Debug, Deserialize)]
struct CollectionQuery {
    pack: Option<String>,
    entity_type: Option<String>,
    limit: Option<i64>,
}

#[derive(Debug, Deserialize)]
struct PackOnlyQuery {
    pack: Option<String>,
    limit: Option<i64>,
}

#[derive(Debug, Serialize, Deserialize)]
struct SourceCandidate {
    url: String,
    title: String,
    #[serde(default)]
    publisher: Option<String>,
    #[serde(default)]
    published_at: Option<String>,
    #[serde(default)]
    excerpt: Option<String>,
}

#[derive(Debug, Deserialize)]
struct ProposalInput {
    pack: Option<String>,
    kind: String,
    payload: Value,
    source: Option<SourceCandidate>,
    idempotency_key: Option<String>,
}

#[tokio::main]
async fn main() {
    let database_url = env::var("DATABASE_URL").expect("DATABASE_URL is required");
    let pool = PgPool::connect(&database_url)
        .await
        .expect("database connection failed");

    let packs_dir = PathBuf::from(env::var("PACKS_DIR").unwrap_or_else(|_| "packs".into()));
    let default_pack = env::var("DEFAULT_PACK").unwrap_or_else(|_| "example".into());
    load_pack(&packs_dir, &default_pack)
        .unwrap_or_else(|error| panic!("DEFAULT_PACK {default_pack:?} is invalid: {error}"));

    let writes_enabled = env_flag("WRITE_API_ENABLED");
    let write_key = env::var("IWM_WRITE_KEY").ok().filter(|value| !value.is_empty());
    if writes_enabled && write_key.is_none() {
        panic!("WRITE_API_ENABLED=true requires IWM_WRITE_KEY");
    }

    let state = AppState {
        pool,
        packs_dir,
        default_pack,
        writes_enabled,
        write_key,
    };

    let app = router(state);
    let port = env::var("API_PORT")
        .ok()
        .and_then(|value| value.parse().ok())
        .unwrap_or(8080);
    let address = SocketAddr::from(([0, 0, 0, 0], port));
    let listener = tokio::net::TcpListener::bind(address).await.unwrap();
    println!("industry-world-model API v0.2 listening on {address}");
    axum::serve(listener, app).await.unwrap();
}

fn router(state: AppState) -> Router {
    Router::new()
        .route("/health", get(health))
        .route("/api/v1/meta", get(meta))
        .route("/api/v1/packs", get(packs))
        .route("/api/v1/packs/{pack}", get(pack))
        .route("/api/v1/entities", get(entities))
        .route("/api/v1/entities/{id}", get(entity))
        .route("/api/v1/relations", get(relations))
        .route("/api/v1/events", get(events))
        .route("/api/v1/timeline", get(events))
        .route("/api/v1/graph", get(graph))
        .route("/api/v1/review-tasks", get(review_tasks))
        .route("/api/v1/ingest/proposals", post(submit_proposal))
        .layer(CorsLayer::permissive())
        .with_state(state)
}

async fn health(State(state): State<AppState>) -> Result<Json<Value>, ApiError> {
    sqlx::query_scalar::<_, i32>("SELECT 1")
        .fetch_one(&state.pool)
        .await?;
    let pack = load_pack(&state.packs_dir, &state.default_pack).map_err(ApiError::bad_request)?;
    Ok(Json(json!({
        "status": "ok",
        "database": "ok",
        "version": "0.2.0",
        "defaultPack": pack.name,
        "writesEnabled": state.writes_enabled
    })))
}

async fn meta(State(state): State<AppState>) -> Result<Json<Value>, ApiError> {
    let (entities, sources, claims, relations, events, review_tasks) =
        sqlx::query_as::<_, (i64, i64, i64, i64, i64, i64)>(
            "SELECT (SELECT COUNT(*) FROM entities),
                    (SELECT COUNT(*) FROM sources),
                    (SELECT COUNT(*) FROM claims),
                    (SELECT COUNT(*) FROM relations),
                    (SELECT COUNT(*) FROM events),
                    (SELECT COUNT(*) FROM review_tasks WHERE status = 'open')",
        )
        .fetch_one(&state.pool)
        .await?;
    Ok(Json(json!({
        "schemaVersion": "0.2",
        "defaultPack": state.default_pack,
        "writesEnabled": state.writes_enabled,
        "counts": {
            "entities": entities,
            "sources": sources,
            "claims": claims,
            "relations": relations,
            "events": events,
            "openReviewTasks": review_tasks
        }
    })))
}

async fn packs(State(state): State<AppState>) -> Result<Json<Value>, ApiError> {
    let mut loaded = Vec::new();
    let mut invalid = Vec::new();
    let entries = fs::read_dir(&state.packs_dir)
        .map_err(|error| ApiError::bad_request(format!("cannot read packs directory: {error}")))?;
    for entry in entries.flatten() {
        if !entry.path().is_dir() {
            continue;
        }
        let name = entry.file_name().to_string_lossy().to_string();
        if !entry.path().join("domain.yaml").is_file() {
            continue;
        }
        match load_pack(&state.packs_dir, &name) {
            Ok(pack) => loaded.push(json!({
                "name": pack.name,
                "title": pack.title,
                "version": pack.version,
                "entityTypes": pack.entities.len(),
                "relationTypes": pack.relations.len(),
                "eventTypes": pack.events.len(),
                "default": name == state.default_pack
            })),
            Err(error) => invalid.push(json!({ "name": name, "error": error })),
        }
    }
    loaded.sort_by(|a, b| a["name"].as_str().cmp(&b["name"].as_str()));
    Ok(Json(json!({ "packs": loaded, "invalid": invalid })))
}

async fn pack(
    State(state): State<AppState>,
    Path(pack_name): Path<String>,
) -> Result<Json<Value>, ApiError> {
    let pack = load_pack(&state.packs_dir, &pack_name).map_err(ApiError::not_found)?;
    Ok(Json(serde_json::to_value(pack).expect("pack serializes")))
}

async fn entities(
    State(state): State<AppState>,
    Query(query): Query<CollectionQuery>,
) -> Result<Json<Value>, ApiError> {
    let pack_name = selected_pack(&state, query.pack)?;
    let limit = clamp_limit(query.limit, 200, 500);
    if let Some(entity_type) = &query.entity_type {
        let pack = load_pack(&state.packs_dir, &pack_name).map_err(ApiError::bad_request)?;
        if !pack.entities.contains_key(entity_type) {
            return Err(ApiError::bad_request(format!(
                "entity type {entity_type:?} is not declared by pack {pack_name:?}"
            )));
        }
    }

    let rows = sqlx::query(
        "SELECT id::text AS id, pack, entity_type, entity_key, name, description,
                status, attributes::text AS attributes
         FROM entities
         WHERE pack = $1 AND ($2::text IS NULL OR entity_type = $2)
         ORDER BY entity_type, name
         LIMIT $3",
    )
    .bind(&pack_name)
    .bind(&query.entity_type)
    .bind(limit)
    .fetch_all(&state.pool)
    .await?;

    let items: Vec<Value> = rows
        .iter()
        .map(|row| {
            json!({
                "id": row.get::<String, _>("id"),
                "pack": row.get::<String, _>("pack"),
                "entityType": row.get::<String, _>("entity_type"),
                "entityKey": row.get::<String, _>("entity_key"),
                "name": row.get::<String, _>("name"),
                "description": row.get::<Option<String>, _>("description"),
                "status": row.get::<String, _>("status"),
                "attributes": parse_json(row.get::<String, _>("attributes"))
            })
        })
        .collect();
    Ok(Json(json!({ "pack": pack_name, "items": items })))
}

async fn entity(
    State(state): State<AppState>,
    Path(id): Path<String>,
) -> Result<Json<Value>, ApiError> {
    let row = sqlx::query(
        "SELECT id::text AS id, pack, entity_type, entity_key, name, description,
                status, attributes::text AS attributes
         FROM entities WHERE id = $1::uuid",
    )
    .bind(&id)
    .fetch_optional(&state.pool)
    .await?
    .ok_or_else(|| ApiError::not_found("entity not found"))?;

    let claims = sqlx::query(
        "SELECT id::text AS id, predicate, value::text AS value, unit, confidence::text AS confidence,
                status, valid_from::text AS valid_from, valid_to::text AS valid_to
         FROM claims WHERE subject_id = $1::uuid ORDER BY predicate, created_at DESC",
    )
    .bind(&id)
    .fetch_all(&state.pool)
    .await?;

    let outgoing = sqlx::query(
        "SELECT r.id::text AS id, r.predicate, r.status,
                o.id::text AS object_id, o.entity_type AS object_type, o.name AS object_name
         FROM relations r JOIN entities o ON o.id = r.object_id
         WHERE r.subject_id = $1::uuid ORDER BY r.predicate, o.name",
    )
    .bind(&id)
    .fetch_all(&state.pool)
    .await?;

    let incoming = sqlx::query(
        "SELECT r.id::text AS id, r.predicate, r.status,
                s.id::text AS subject_id, s.entity_type AS subject_type, s.name AS subject_name
         FROM relations r JOIN entities s ON s.id = r.subject_id
         WHERE r.object_id = $1::uuid ORDER BY r.predicate, s.name",
    )
    .bind(&id)
    .fetch_all(&state.pool)
    .await?;

    let event_rows = sqlx::query(
        "SELECT e.id::text AS id, e.event_type, e.event_key, e.title, e.summary,
                e.occurred_on::text AS occurred_on, e.status, ee.role
         FROM event_entities ee JOIN events e ON e.id = ee.event_id
         WHERE ee.entity_id = $1::uuid
         ORDER BY e.occurred_on DESC NULLS LAST, e.created_at DESC
         LIMIT 100",
    )
    .bind(&id)
    .fetch_all(&state.pool)
    .await?;

    Ok(Json(json!({
        "id": row.get::<String, _>("id"),
        "pack": row.get::<String, _>("pack"),
        "entityType": row.get::<String, _>("entity_type"),
        "entityKey": row.get::<String, _>("entity_key"),
        "name": row.get::<String, _>("name"),
        "description": row.get::<Option<String>, _>("description"),
        "status": row.get::<String, _>("status"),
        "attributes": parse_json(row.get::<String, _>("attributes")),
        "claims": claims.iter().map(|row| json!({
            "id": row.get::<String, _>("id"),
            "predicate": row.get::<String, _>("predicate"),
            "value": parse_json(row.get::<String, _>("value")),
            "unit": row.get::<Option<String>, _>("unit"),
            "confidence": row.get::<Option<String>, _>("confidence"),
            "status": row.get::<String, _>("status"),
            "validFrom": row.get::<Option<String>, _>("valid_from"),
            "validTo": row.get::<Option<String>, _>("valid_to")
        })).collect::<Vec<_>>(),
        "relations": {
            "outgoing": outgoing.iter().map(|row| json!({
                "id": row.get::<String, _>("id"),
                "predicate": row.get::<String, _>("predicate"),
                "status": row.get::<String, _>("status"),
                "object": {
                    "id": row.get::<String, _>("object_id"),
                    "entityType": row.get::<String, _>("object_type"),
                    "name": row.get::<String, _>("object_name")
                }
            })).collect::<Vec<_>>(),
            "incoming": incoming.iter().map(|row| json!({
                "id": row.get::<String, _>("id"),
                "predicate": row.get::<String, _>("predicate"),
                "status": row.get::<String, _>("status"),
                "subject": {
                    "id": row.get::<String, _>("subject_id"),
                    "entityType": row.get::<String, _>("subject_type"),
                    "name": row.get::<String, _>("subject_name")
                }
            })).collect::<Vec<_>>()
        },
        "events": event_rows.iter().map(event_json).collect::<Vec<_>>()
    })))
}

async fn relations(
    State(state): State<AppState>,
    Query(query): Query<PackOnlyQuery>,
) -> Result<Json<Value>, ApiError> {
    let pack_name = selected_pack(&state, query.pack)?;
    let limit = clamp_limit(query.limit, 300, 1000);
    let rows = relation_rows(&state.pool, &pack_name, limit).await?;
    Ok(Json(json!({
        "pack": pack_name,
        "items": rows.iter().map(relation_json).collect::<Vec<_>>()
    })))
}

async fn events(
    State(state): State<AppState>,
    Query(query): Query<PackOnlyQuery>,
) -> Result<Json<Value>, ApiError> {
    let pack_name = selected_pack(&state, query.pack)?;
    let limit = clamp_limit(query.limit, 200, 500);
    let rows = sqlx::query(
        "SELECT id::text AS id, event_type, event_key, title, summary,
                occurred_on::text AS occurred_on, occurred_end::text AS occurred_end,
                date_precision, classification, status, attributes::text AS attributes
         FROM events WHERE pack = $1
         ORDER BY occurred_on DESC NULLS LAST, created_at DESC
         LIMIT $2",
    )
    .bind(&pack_name)
    .bind(limit)
    .fetch_all(&state.pool)
    .await?;
    Ok(Json(json!({
        "pack": pack_name,
        "items": rows.iter().map(event_json).collect::<Vec<_>>()
    })))
}

async fn graph(
    State(state): State<AppState>,
    Query(query): Query<PackOnlyQuery>,
) -> Result<Json<Value>, ApiError> {
    let pack_name = selected_pack(&state, query.pack)?;
    let node_limit = clamp_limit(query.limit, 300, 500);
    let nodes = sqlx::query(
        "SELECT id::text AS id, entity_type, entity_key, name, status
         FROM entities WHERE pack = $1 ORDER BY entity_type, name LIMIT $2",
    )
    .bind(&pack_name)
    .bind(node_limit)
    .fetch_all(&state.pool)
    .await?;
    let edges = relation_rows(&state.pool, &pack_name, 1000).await?;
    let node_ids: HashSet<String> = nodes.iter().map(|row| row.get::<String, _>("id")).collect();
    Ok(Json(json!({
        "pack": pack_name,
        "nodes": nodes.iter().map(|row| json!({
            "id": row.get::<String, _>("id"),
            "entityType": row.get::<String, _>("entity_type"),
            "entityKey": row.get::<String, _>("entity_key"),
            "name": row.get::<String, _>("name"),
            "status": row.get::<String, _>("status")
        })).collect::<Vec<_>>(),
        "edges": edges.iter().filter_map(|row| {
            let subject_id = row.get::<String, _>("subject_id");
            let object_id = row.get::<String, _>("object_id");
            if node_ids.contains(&subject_id) && node_ids.contains(&object_id) {
                Some(json!({
                    "id": row.get::<String, _>("id"),
                    "source": subject_id,
                    "target": object_id,
                    "predicate": row.get::<String, _>("predicate"),
                    "status": row.get::<String, _>("status")
                }))
            } else {
                None
            }
        }).collect::<Vec<_>>()
    })))
}

async fn review_tasks(
    State(state): State<AppState>,
    Query(query): Query<PackOnlyQuery>,
) -> Result<Json<Value>, ApiError> {
    let pack_name = query.pack.unwrap_or_else(|| state.default_pack.clone());
    load_pack(&state.packs_dir, &pack_name).map_err(ApiError::bad_request)?;
    let limit = clamp_limit(query.limit, 100, 300);
    let rows = sqlx::query(
        "SELECT rt.id::text AS id, rt.reason, rt.status, rt.assigned_to, rt.decision_note,
                rt.created_at::text AS created_at, ij.id::text AS job_id, ij.pack,
                ij.status AS job_status, ij.idempotency_key, ij.stats::text AS stats
         FROM review_tasks rt
         JOIN ingest_jobs ij ON rt.target_kind = 'ingest_job' AND rt.target_id = ij.id
         WHERE ij.pack = $1
         ORDER BY rt.created_at DESC
         LIMIT $2",
    )
    .bind(&pack_name)
    .bind(limit)
    .fetch_all(&state.pool)
    .await?;
    Ok(Json(json!({
        "pack": pack_name,
        "items": rows.iter().map(|row| json!({
            "id": row.get::<String, _>("id"),
            "reason": row.get::<String, _>("reason"),
            "status": row.get::<String, _>("status"),
            "assignedTo": row.get::<Option<String>, _>("assigned_to"),
            "decisionNote": row.get::<Option<String>, _>("decision_note"),
            "createdAt": row.get::<String, _>("created_at"),
            "job": {
                "id": row.get::<String, _>("job_id"),
                "status": row.get::<String, _>("job_status"),
                "idempotencyKey": row.get::<String, _>("idempotency_key"),
                "candidate": parse_json(row.get::<String, _>("stats"))
            }
        })).collect::<Vec<_>>()
    })))
}

async fn submit_proposal(
    State(state): State<AppState>,
    headers: HeaderMap,
    Json(input): Json<ProposalInput>,
) -> Result<(StatusCode, Json<Value>), ApiError> {
    authorize_write(&state, &headers)?;
    let pack_name = selected_pack(&state, input.pack.clone())?;
    let pack = load_pack(&state.packs_dir, &pack_name).map_err(ApiError::bad_request)?;
    validate_proposal(&pack, &input)?;

    let idempotency_key = input.idempotency_key.clone().unwrap_or_else(|| {
        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default()
            .as_nanos();
        format!("{}-{}-{now}", pack_name, input.kind)
    });

    let candidate = json!({
        "kind": input.kind,
        "payload": input.payload,
        "source": input.source
    });
    let candidate_text = serde_json::to_string(&candidate).expect("candidate serializes");
    let input_uri = candidate["source"]["url"].as_str().map(str::to_owned);

    let mut transaction = state.pool.begin().await?;
    if let Some(existing) = sqlx::query(
        "SELECT id::text AS id, status FROM ingest_jobs WHERE idempotency_key = $1",
    )
    .bind(&idempotency_key)
    .fetch_optional(&mut *transaction)
    .await?
    {
        let job_id = existing.get::<String, _>("id");
        let review = sqlx::query(
            "SELECT id::text AS id FROM review_tasks
             WHERE target_kind = 'ingest_job' AND target_id = $1::uuid
             ORDER BY created_at DESC LIMIT 1",
        )
        .bind(&job_id)
        .fetch_optional(&mut *transaction)
        .await?;
        transaction.commit().await?;
        return Ok((
            StatusCode::OK,
            Json(json!({
                "jobId": job_id,
                "reviewTaskId": review.map(|row| row.get::<String, _>("id")),
                "status": existing.get::<String, _>("status"),
                "duplicate": true
            })),
        ));
    }

    let job_id = sqlx::query(
        "INSERT INTO ingest_jobs (pack, input_uri, status, idempotency_key, stats)
         VALUES ($1, $2, 'review', $3, $4::jsonb)
         RETURNING id::text AS id",
    )
    .bind(&pack_name)
    .bind(&input_uri)
    .bind(&idempotency_key)
    .bind(&candidate_text)
    .fetch_one(&mut *transaction)
    .await?
    .get::<String, _>("id");

    let review_id = sqlx::query(
        "INSERT INTO review_tasks (target_kind, target_id, reason)
         VALUES ('ingest_job', $1::uuid, 'agent proposal requires review')
         RETURNING id::text AS id",
    )
    .bind(&job_id)
    .fetch_one(&mut *transaction)
    .await?
    .get::<String, _>("id");

    sqlx::query(
        "INSERT INTO change_logs (actor, action, target_kind, target_id, after_state, reason)
         VALUES ('agent-api', 'proposal.submitted', 'ingest_job', $1::uuid, $2::jsonb,
                 'pack-validated candidate queued for review')",
    )
    .bind(&job_id)
    .bind(&candidate_text)
    .execute(&mut *transaction)
    .await?;

    transaction.commit().await?;
    Ok((
        StatusCode::ACCEPTED,
        Json(json!({
            "jobId": job_id,
            "reviewTaskId": review_id,
            "status": "review",
            "duplicate": false
        })),
    ))
}

async fn relation_rows(pool: &PgPool, pack: &str, limit: i64) -> Result<Vec<sqlx::postgres::PgRow>, ApiError> {
    Ok(sqlx::query(
        "SELECT r.id::text AS id, r.predicate, r.status,
                s.id::text AS subject_id, s.entity_type AS subject_type, s.name AS subject_name,
                o.id::text AS object_id, o.entity_type AS object_type, o.name AS object_name
         FROM relations r
         JOIN entities s ON s.id = r.subject_id
         JOIN entities o ON o.id = r.object_id
         WHERE s.pack = $1 AND o.pack = $1
         ORDER BY r.predicate, s.name, o.name
         LIMIT $2",
    )
    .bind(pack)
    .bind(limit)
    .fetch_all(pool)
    .await?)
}

fn relation_json(row: &sqlx::postgres::PgRow) -> Value {
    json!({
        "id": row.get::<String, _>("id"),
        "predicate": row.get::<String, _>("predicate"),
        "status": row.get::<String, _>("status"),
        "subject": {
            "id": row.get::<String, _>("subject_id"),
            "entityType": row.get::<String, _>("subject_type"),
            "name": row.get::<String, _>("subject_name")
        },
        "object": {
            "id": row.get::<String, _>("object_id"),
            "entityType": row.get::<String, _>("object_type"),
            "name": row.get::<String, _>("object_name")
        }
    })
}

fn event_json(row: &sqlx::postgres::PgRow) -> Value {
    let mut value = json!({
        "id": row.get::<String, _>("id"),
        "eventType": row.get::<String, _>("event_type"),
        "eventKey": row.get::<String, _>("event_key"),
        "title": row.get::<String, _>("title"),
        "summary": row.get::<Option<String>, _>("summary"),
        "occurredOn": row.get::<Option<String>, _>("occurred_on"),
        "status": row.get::<String, _>("status")
    });
    if let Ok(occurred_end) = row.try_get::<Option<String>, _>("occurred_end") {
        value["occurredEnd"] = json!(occurred_end);
    }
    if let Ok(date_precision) = row.try_get::<String, _>("date_precision") {
        value["datePrecision"] = json!(date_precision);
    }
    if let Ok(classification) = row.try_get::<String, _>("classification") {
        value["classification"] = json!(classification);
    }
    if let Ok(attributes) = row.try_get::<String, _>("attributes") {
        value["attributes"] = parse_json(attributes);
    }
    if let Ok(role) = row.try_get::<String, _>("role") {
        value["role"] = json!(role);
    }
    value
}

fn selected_pack(state: &AppState, requested: Option<String>) -> Result<String, ApiError> {
    let name = requested.unwrap_or_else(|| state.default_pack.clone());
    load_pack(&state.packs_dir, &name).map_err(ApiError::bad_request)?;
    Ok(name)
}

fn load_pack(root: &FsPath, name: &str) -> Result<DomainPack, String> {
    if name.is_empty()
        || !name
            .chars()
            .all(|character| character.is_ascii_alphanumeric() || character == '-' || character == '_')
    {
        return Err("pack name contains unsupported characters".into());
    }
    let path = root.join(name).join("domain.yaml");
    let content = fs::read_to_string(&path)
        .map_err(|error| format!("cannot read {}: {error}", path.display()))?;
    parse_pack(name, &content)
}

fn parse_pack(expected_name: &str, content: &str) -> Result<DomainPack, String> {
    let pack: DomainPack = serde_yaml::from_str(content).map_err(|error| error.to_string())?;
    validate_pack(expected_name, &pack)?;
    Ok(pack)
}

fn validate_pack(expected_name: &str, pack: &DomainPack) -> Result<(), String> {
    if pack.name != expected_name {
        return Err(format!(
            "domain name {:?} must match directory {:?}",
            pack.name, expected_name
        ));
    }
    if pack.title.trim().is_empty() || pack.version.trim().is_empty() {
        return Err("title and version are required".into());
    }
    if pack.entities.is_empty() {
        return Err("at least one entity type is required".into());
    }
    ensure_unique("claim", &pack.claims)?;
    ensure_unique("event", &pack.events)?;
    ensure_unique("event relation", &pack.event_relations)?;

    let mut relation_keys = HashSet::new();
    for relation in &pack.relations {
        if !pack.entities.contains_key(&relation.subject) {
            return Err(format!("relation subject {:?} is not an entity type", relation.subject));
        }
        if !pack.entities.contains_key(&relation.object) {
            return Err(format!("relation object {:?} is not an entity type", relation.object));
        }
        let key = format!("{}:{}:{}", relation.subject, relation.predicate, relation.object);
        if !relation_keys.insert(key.clone()) {
            return Err(format!("duplicate relation rule {key}"));
        }
    }
    Ok(())
}

fn ensure_unique(label: &str, values: &[String]) -> Result<(), String> {
    let mut seen = HashSet::new();
    for value in values {
        if value.trim().is_empty() {
            return Err(format!("{label} names cannot be empty"));
        }
        if !seen.insert(value) {
            return Err(format!("duplicate {label} {value:?}"));
        }
    }
    Ok(())
}

fn validate_proposal(pack: &DomainPack, input: &ProposalInput) -> Result<(), ApiError> {
    match input.kind.as_str() {
        "entity" => {
            let entity_type = required_payload_string(&input.payload, "entity_type")?;
            if !pack.entities.contains_key(entity_type) {
                return Err(ApiError::bad_request(format!(
                    "entity_type {entity_type:?} is not declared by pack {:?}",
                    pack.name
                )));
            }
        }
        "claim" => {
            let predicate = required_payload_string(&input.payload, "predicate")?;
            if !pack.claims.iter().any(|item| item == predicate) {
                return Err(ApiError::bad_request(format!(
                    "claim predicate {predicate:?} is not declared by pack {:?}",
                    pack.name
                )));
            }
            require_source(input)?;
        }
        "relation" => {
            let subject = required_payload_string(&input.payload, "subject_type")?;
            let predicate = required_payload_string(&input.payload, "predicate")?;
            let object = required_payload_string(&input.payload, "object_type")?;
            if !pack.relations.iter().any(|rule| {
                rule.subject == subject && rule.predicate == predicate && rule.object == object
            }) {
                return Err(ApiError::bad_request(format!(
                    "relation rule {subject}:{predicate}:{object} is not declared by pack {:?}",
                    pack.name
                )));
            }
            require_source(input)?;
        }
        "event" => {
            let event_type = required_payload_string(&input.payload, "event_type")?;
            if !pack.events.iter().any(|item| item == event_type) {
                return Err(ApiError::bad_request(format!(
                    "event_type {event_type:?} is not declared by pack {:?}",
                    pack.name
                )));
            }
            require_source(input)?;
        }
        "media_asset" => require_source(input)?,
        other => {
            return Err(ApiError::bad_request(format!(
                "unsupported proposal kind {other:?}; expected entity, claim, relation, event, or media_asset"
            )));
        }
    }
    Ok(())
}

fn required_payload_string<'a>(payload: &'a Value, key: &str) -> Result<&'a str, ApiError> {
    payload
        .get(key)
        .and_then(Value::as_str)
        .filter(|value| !value.trim().is_empty())
        .ok_or_else(|| ApiError::bad_request(format!("payload.{key} is required")))
}

fn require_source(input: &ProposalInput) -> Result<(), ApiError> {
    let source = input
        .source
        .as_ref()
        .ok_or_else(|| ApiError::bad_request(format!("{} proposals require source evidence", input.kind)))?;
    if !(source.url.starts_with("https://") || source.url.starts_with("http://")) {
        return Err(ApiError::bad_request("source.url must be http(s)"));
    }
    if source.title.trim().is_empty() {
        return Err(ApiError::bad_request("source.title is required"));
    }
    Ok(())
}

fn authorize_write(state: &AppState, headers: &HeaderMap) -> Result<(), ApiError> {
    if !state.writes_enabled {
        return Err(ApiError::forbidden(
            "proposal writes are disabled; set WRITE_API_ENABLED=true and IWM_WRITE_KEY to enable",
        ));
    }
    let expected = state.write_key.as_deref().unwrap_or_default();
    let provided = headers
        .get("x-iwm-key")
        .and_then(|value| value.to_str().ok())
        .unwrap_or_default();
    if provided != expected {
        return Err(ApiError::forbidden("invalid x-iwm-key"));
    }
    Ok(())
}

fn clamp_limit(value: Option<i64>, default: i64, maximum: i64) -> i64 {
    value.unwrap_or(default).clamp(1, maximum)
}

fn parse_json(value: String) -> Value {
    serde_json::from_str(&value).unwrap_or(Value::Null)
}

fn env_flag(name: &str) -> bool {
    env::var(name)
        .map(|value| matches!(value.to_ascii_lowercase().as_str(), "1" | "true" | "yes" | "on"))
        .unwrap_or(false)
}

struct ApiError {
    status: StatusCode,
    message: String,
}

impl ApiError {
    fn bad_request(message: impl Into<String>) -> Self {
        Self { status: StatusCode::BAD_REQUEST, message: message.into() }
    }

    fn not_found(message: impl Into<String>) -> Self {
        Self { status: StatusCode::NOT_FOUND, message: message.into() }
    }

    fn forbidden(message: impl Into<String>) -> Self {
        Self { status: StatusCode::FORBIDDEN, message: message.into() }
    }
}

impl From<sqlx::Error> for ApiError {
    fn from(error: sqlx::Error) -> Self {
        eprintln!("database error: {error}");
        Self {
            status: StatusCode::SERVICE_UNAVAILABLE,
            message: "database unavailable".into(),
        }
    }
}

impl IntoResponse for ApiError {
    fn into_response(self) -> Response {
        (self.status, Json(json!({ "error": self.message }))).into_response()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    const VALID: &str = r#"
name: test
title: Test Pack
version: 0.2.0
entities:
  company:
    label: Company
    fields: [website]
  product:
    label: Product
    fields: [release_date]
claims: [website, release_date]
relations:
  - subject: company
    predicate: produces
    object: product
events: [product_release]
"#;

    #[test]
    fn parses_valid_pack() {
        let pack = parse_pack("test", VALID).unwrap();
        assert_eq!(pack.name, "test");
        assert!(pack.entities.contains_key("product"));
    }

    #[test]
    fn rejects_relation_with_unknown_entity_type() {
        let invalid = VALID.replace("object: product", "object: missing");
        let error = parse_pack("test", &invalid).unwrap_err();
        assert!(error.contains("not an entity type"));
    }

    #[test]
    fn rejects_directory_name_mismatch() {
        let error = parse_pack("other", VALID).unwrap_err();
        assert!(error.contains("must match directory"));
    }
}
