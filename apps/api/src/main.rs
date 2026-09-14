use axum::{
    Json, Router,
    extract::State,
    http::StatusCode,
    response::{IntoResponse, Response},
    routing::get,
};
use serde_json::{Value, json};
use sqlx::PgPool;
use std::{env, net::SocketAddr};

#[tokio::main]
async fn main() {
    let database_url = env::var("DATABASE_URL").expect("DATABASE_URL is required");
    let pool = PgPool::connect(&database_url)
        .await
        .expect("database connection failed");
    let app = router(pool);
    let port = env::var("API_PORT")
        .ok()
        .and_then(|value| value.parse().ok())
        .unwrap_or(8080);
    let address = SocketAddr::from(([0, 0, 0, 0], port));
    let listener = tokio::net::TcpListener::bind(address).await.unwrap();
    println!("industry-world-model API listening on {address}");
    axum::serve(listener, app).await.unwrap();
}

fn router(pool: PgPool) -> Router {
    Router::new()
        .route("/health", get(health))
        .route("/api/v1/meta", get(meta))
        .with_state(pool)
}

async fn health(State(pool): State<PgPool>) -> Result<Json<Value>, ApiError> {
    sqlx::query_scalar::<_, i32>("SELECT 1")
        .fetch_one(&pool)
        .await?;
    Ok(Json(json!({ "status": "ok", "database": "ok" })))
}

async fn meta(State(pool): State<PgPool>) -> Result<Json<Value>, ApiError> {
    let (entities, sources, events) = sqlx::query_as::<_, (i64, i64, i64)>(
        "SELECT (SELECT COUNT(*) FROM entities),
                (SELECT COUNT(*) FROM sources),
                (SELECT COUNT(*) FROM events)",
    )
    .fetch_one(&pool)
    .await?;
    Ok(Json(json!({
        "schemaVersion": "0.1",
        "counts": { "entities": entities, "sources": sources, "events": events }
    })))
}

struct ApiError(sqlx::Error);

impl From<sqlx::Error> for ApiError {
    fn from(error: sqlx::Error) -> Self {
        Self(error)
    }
}

impl IntoResponse for ApiError {
    fn into_response(self) -> Response {
        eprintln!("database error: {}", self.0);
        (
            StatusCode::SERVICE_UNAVAILABLE,
            Json(json!({ "error": "database unavailable" })),
        )
            .into_response()
    }
}
