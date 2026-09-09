# Operations

## Local run

```bash
cp .env.example .env          # adjust SECRET_KEY for anything shared
docker compose up -d --build  # api runs `alembic upgrade head` on start
docker compose ps             # all services healthy
```

- Control plane: <http://localhost:5173> — the SPA and its API calls share this
  origin; Nginx proxies `/api` and `/ws` to the API service.
- API docs (Swagger): <http://localhost:8000/docs>
- Prometheus metrics: <http://localhost:8000/metrics>

Run the test suite and quality gates:

```bash
docker compose exec api pytest -q
docker compose exec api ruff check app
docker compose exec api ruff format --check app
```

## Configuration

All configuration is environment-driven (`app/core/config.py`). Nothing is
hard-coded; there are no credentials in the image.

| Variable | Default | Purpose |
| --- | --- | --- |
| `SECRET_KEY` | — (required, ≥32 chars) | JWT signing key |
| `ACCESS_TOKEN_MINUTES` | `30` | Access-token lifetime |
| `ENVIRONMENT` | `development` | Reported in telemetry resource attributes |
| `DATABASE_URL` | `postgresql+asyncpg://agentic:agentic@postgres:5432/agentic` | Async PostgreSQL DSN |
| `REDIS_URL` | `redis://redis:6379/0` | Queue + pub/sub |
| `QDRANT_URL` | `http://qdrant:6333` | Vector store |
| `CORS_ORIGINS` | `["http://localhost:5173"]` | Allowed browser origins (JSON list or comma-separated) |
| `DEMO_TTL_MINUTES` | `120` | Demo-tenant expiry |
| `INVITATION_TTL_HOURS` | `48` | Invitation-token expiry |
| `RUN_TIMEOUT_SECONDS` | `120` | Per-agent-call timeout |
| `MAX_CONCURRENCY` | `8` | Upper bound on parallel node execution per run |
| `LLM_PROVIDER` | `local` | `local` (deterministic) or `openai` / `openai-compatible` |
| `LLM_BASE_URL` / `LLM_API_KEY` / `LLM_MODEL` | empty | Required only for a remote provider |
| `TOOL_ALLOWED_HOSTS` | `[]` | Default-deny allowlist for outbound tool HTTP endpoints |
| `TOOL_TIMEOUT_SECONDS` / `TOOL_MAX_RETRIES` | `30` / `2` | Tool-call bounds |
| `OTEL_ENABLED` | `true` | Enable OpenTelemetry tracing |
| `OTEL_EXPORTER_ENDPOINT` | empty | OTLP/HTTP collector; without it, spans use a console exporter |
| `MEMORY_VECTOR_SIZE` | `64` | Local embedding dimensionality |

## Observability

- **Correlation IDs** — `X-Correlation-ID` is generated or propagated per
  request and bound to every structured log line for that request.
- **Logs** — single-line JSON (`structlog`) to stdout.
- **Traces/metrics** — OpenTelemetry instruments FastAPI and SQLAlchemy; set
  `OTEL_EXPORTER_ENDPOINT` to ship OTLP spans. Prometheus metrics at `/metrics`.
- **Health** — `/health/live` (process), `/health/ready` (pings Redis).
- **Run progress** — persisted in `run_events` and streamed over
  `WS /ws/runs/{id}`.

## Deployment (Kubernetes)

`k8s/` contains namespace, config/secret templates, API/worker/frontend
deployments, ingress and an HPA. For production:

1. Replace the example images with your registry references.
2. Point `DATABASE_URL`, `REDIS_URL`, `QDRANT_URL` at managed/hardened services.
3. Inject `SECRET_KEY` and any `LLM_*` values from the cluster secret manager —
   never commit secret values.
4. Run `alembic upgrade head` as a migration job (or rely on the API start
   command in low-risk environments).
5. Set `OTEL_EXPORTER_ENDPOINT` to your collector.

## Runbook

| Symptom | Check |
| --- | --- |
| API not `ready` | `docker compose logs api`; Redis reachable? migrations applied (`alembic current`)? |
| Runs stay `queued` | Worker running? `docker compose logs worker`; Redis `LLEN agentic:runs` |
| Run `timed_out` | `RUN_TIMEOUT_SECONDS` too low, or the LLM provider is slow/unreachable |
| Tool call fails with a permission error | Missing `ToolPermission` grant, or endpoint host not in `TOOL_ALLOWED_HOSTS` |
| Run stuck `waiting_approval` | Pending row in `/approvals`; an approver must decide |
| Frontend cannot reach API | Nginx proxy healthy? `docker compose logs frontend`; API service name resolvable as `api` on the compose network |

## Known limitations

- **LLM provider** — the default `local` provider is deterministic and offline.
  A real provider must be configured via `LLM_*` for meaningful agent output.
- **Embeddings** — the memory service uses a deterministic hash embedding for
  local development. Swap `app/services/memory.py::embed` for a model endpoint
  in production.
- **Type checking** — `mypy` runs advisory-only against a pragmatic baseline
  rather than `strict`; see [backend.md](backend.md#type-checking).
- **Evaluation datasets** — scoring is exact/partial field match on structured
  output; semantic scorers are a follow-up.
- **Runtime scale** — no published load benchmarks; concurrency is bounded but
  capacity planning has not been done.
- **Docker daemon** — this repository's development environment builds and runs
  the full Compose stack; there is no separate hosted environment.
