# Enterprise Agentic AI Operating Platform

A production-oriented control plane for building, orchestrating and operating
enterprise AI agents and multi-agent workflows: agent and tool registries,
default-deny tool authorization, DAG workflow orchestration with bounded
parallel execution, human approval gates, reproducible evaluations with
regression gates, tenant-isolated memory, live run streaming and a complete
audit trail.

Full documentation is in [`docs/`](docs/README.md) — product, business and
technical.

## Architecture

```
        Browser ── http://localhost:5173 ──▶ Nginx (SPA + reverse proxy)
                                               │ /api, /ws  ──▶
        ┌──────────────────────────────────────▼──┐
        │   FastAPI  (:8000)      │   /api/v1 · /ws/runs/{id} · /metrics
        │  auth · RBAC · policy   │
        │  domain services        │
        └──┬────────┬────────┬────┘
           │        │        │
    ┌──────▼──┐ ┌───▼───┐ ┌──▼─────┐
    │Postgres │ │ Redis │ │ Qdrant │
    │state +  │ │queue +│ │ memory │
    │audit    │ │pubsub │ │vectors │
    └─────────┘ └───┬───┘ └────────┘
                    │ BLPOP
             ┌──────▼──────┐      ┌──────────────┐
             │ run worker  │─────▶│ LLM gateway  │ local / OpenAI-compatible
             │ bounded exec│      └──────────────┘
             └─────────────┘
```

Details: [docs/technical/architecture.md](docs/technical/architecture.md).

## Local setup

Requirements: Docker with Compose.

```bash
cp .env.example .env
# set SECRET_KEY to a random 32+ character string for anything shared
docker compose up -d --build
docker compose ps            # wait for all services to be healthy
```

The `api` service runs `alembic upgrade head` automatically on start.

- Control plane: <http://localhost:5173> — the SPA calls the API on this same
  origin; Nginx proxies `/api` and `/ws` to the API service (no browser CORS).
- API docs (Swagger): <http://localhost:8000/docs>
- Metrics: <http://localhost:8000/metrics>

## Demo walkthrough

1. Open <http://localhost:5173> and choose **Create account** (you become the
   organization owner), or **Guided demo** for a pre-populated, auto-expiring
   tenant.
2. **Projects** → create a project.
3. **Agents** → create an agent → *New version* (system prompt + model) →
   *Publish v1*.
4. **Tools** → register a tool (try risk level *high*). Tools are default-deny.
5. **Workflows** → create a workflow → *Edit definition* (a small DAG) →
   *Save version* (validated for unique ids, resolvable deps, no cycles) →
   *Publish v1*.
6. **Runs** → *Launch run*. Watch lifecycle events stream in the run drawer.
7. If a node used a high-risk tool, the run pauses in **Approvals** — approve it
   and the run resumes.
8. **Evaluations** → create a dataset, *Run now*, attach a regression gate.
9. **Audit log** shows every privileged action; **Observability** documents the
   telemetry signals.

The same flow via the API is in
[docs/product/overview.md](docs/product/overview.md#first-journey-demo-walkthrough).

## Configuration

All configuration is environment-driven; there are no secrets in the image or
the frontend bundle. Full table:
[docs/technical/operations.md#configuration](docs/technical/operations.md#configuration).

| Variable | Default | Purpose |
| --- | --- | --- |
| `SECRET_KEY` | *(required, ≥32 chars)* | JWT signing key |
| `ACCESS_TOKEN_MINUTES` | `30` | Access-token lifetime |
| `DATABASE_URL` | `postgresql+asyncpg://agentic:agentic@postgres:5432/agentic` | PostgreSQL DSN |
| `REDIS_URL` | `redis://redis:6379/0` | Queue + pub/sub |
| `QDRANT_URL` | `http://qdrant:6333` | Vector store |
| `CORS_ORIGINS` | `["http://localhost:5173"]` | Allowed browser origins |
| `RUN_TIMEOUT_SECONDS` | `120` | Per-agent-call timeout |
| `MAX_CONCURRENCY` | `8` | Max parallel nodes per run |
| `LLM_PROVIDER` / `LLM_BASE_URL` / `LLM_API_KEY` / `LLM_MODEL` | `local` / — | LLM provider (default is deterministic and offline) |
| `TOOL_ALLOWED_HOSTS` | `[]` | Default-deny allowlist for outbound tool endpoints |
| `OTEL_ENABLED` / `OTEL_EXPORTER_ENDPOINT` | `true` / — | OpenTelemetry export |

## Tests and quality gates

```bash
docker compose exec api pytest -q
docker compose exec api ruff check app
docker compose exec api ruff format --check app
docker compose exec api mypy app          # advisory
```

CI (`.github/workflows/ci.yml`) runs ruff, format check, migrations and the
pytest suite against PostgreSQL and Redis service containers, plus a frontend
type-check and build.

## Deployment

`k8s/` contains namespace, config/secret templates, API/worker/frontend
deployments, ingress and an HPA. Point `DATABASE_URL`, `REDIS_URL` and
`QDRANT_URL` at managed services, inject `SECRET_KEY` and `LLM_*` from the
cluster secret manager, and run `alembic upgrade head` as a migration job.
See [docs/technical/operations.md#deployment-kubernetes](docs/technical/operations.md#deployment-kubernetes).

## Known limitations

- The default `local` LLM provider is deterministic and offline; configure
  `LLM_*` for a real provider.
- The memory service uses a deterministic hash embedding for local development;
  swap in a model endpoint for production.
- `mypy` runs advisory-only against a pragmatic baseline, not `--strict`.
- Evaluation scoring is exact/partial field match; semantic scorers are planned.
- No published load benchmarks; concurrency is bounded but capacity planning is
  outstanding.

Full list: [docs/technical/operations.md#known-limitations](docs/technical/operations.md#known-limitations).

## Repository layout

```
backend/    FastAPI app, services, worker, Alembic migrations, tests
frontend/   React + TypeScript control plane (Vite)
k8s/        Kubernetes manifests
docs/       product / business / technical documentation
docker-compose.yml
```
