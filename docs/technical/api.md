# API reference

Base URL: `/api/v1`. Interactive schema: `GET /docs` (Swagger) and
`GET /openapi.json`.

## Authentication

All endpoints except registration, login, demo and the protocol discovery
documents require a Bearer token:

```
Authorization: Bearer <access_token>
```

Tokens are HS256 JWTs containing `sub` (user id), `org_id` (organization id) and
`role`, expiring after `ACCESS_TOKEN_MINUTES`. Obtain one from `POST /register`,
`POST /login` or `POST /demo`.

Auth routes are also mounted under `/api/v1/auth/*` (e.g. `/api/v1/auth/login`,
`/api/v1/auth/me`) as a compatibility alias.

## Error envelope

```jsonc
// string detail (business errors)
{ "detail": "A project with that name already exists" }

// validation errors (422)
{ "detail": [ { "loc": ["body", "password"], "msg": "String should have at least 12 characters", "type": "..." } ] }
```

| Status | Meaning |
| --- | --- |
| 400 | Malformed request (e.g. invalid invitation) |
| 401 | Missing/expired/invalid token |
| 403 | Authenticated but insufficient role |
| 404 | Not found **or** outside the caller's organization (tenant isolation) |
| 409 | Conflict (duplicate email/name, idempotency key, already-decided approval, terminal run) |
| 422 | Request or workflow-definition validation failure |

Every response carries `X-Correlation-ID` (echoed from the request or generated).

## Endpoints

### Identity & team

| Method | Path | Notes |
| --- | --- | --- |
| `POST` | `/register` | `{ email, full_name, password (≥12), organization_name }` → `{ access_token }` (201). Caller becomes `owner`. |
| `POST` | `/login` | `{ email, password }` → `{ access_token }` |
| `POST` | `/demo` | `{ organization_name?, full_name? }` → `{ access_token }`; provisions an isolated, auto-expiring demo tenant with sample data |
| `GET` | `/me` | Current user + organization |
| `POST` | `/invite`, `/team/invite` | `{ email, role }` → one-time invitation token (owner/admin only) |
| `POST` | `/accept-invite` | `?token=&full_name=&password=` → `{ access_token }` |
| `GET` | `/team/users` | Organization members |

### Projects, agents, tools, workflows

| Method | Path | Notes |
| --- | --- | --- |
| `GET/POST` | `/projects` | `{ name (≥2), description? }` |
| `GET/POST` | `/projects/{pid}/agents` | `{ name }` |
| `POST` | `/projects/{pid}/agents/{id}/versions` | `{ system_prompt, model_provider, model_name, config }` — new immutable version |
| `POST` | `/projects/{pid}/agents/{id}/versions/{v}/publish` | Marks a single version published; activates the agent |
| `GET/POST` | `/projects/{pid}/tools` | `{ name, description, risk_level: low\|medium\|high, input_schema, endpoint? }` |
| `PUT` | `/projects/{pid}/tools/permissions/{agent_id}` | `{ tool_id, allowed }` — default is deny |
| `GET/POST` | `/projects/{pid}/workflows` | `{ name }` |
| `POST` | `/projects/{pid}/workflows/{id}/versions` | `{ definition }` — validated (unique node ids, resolvable `depends_on`, acyclic) |
| `POST` | `/projects/{pid}/workflows/{id}/versions/{v}/publish` | |

Workflow `definition` shape:

```jsonc
{
  "nodes": [
    { "id": "triage",  "type": "agent", "agent_id": "…" },
    { "id": "act",     "type": "agent", "tool_id": "…", "agent_id": "…", "depends_on": ["triage"] }
  ],
  "max_concurrency": 2
}
```

### Runs

| Method | Path | Notes |
| --- | --- | --- |
| `POST` | `/runs` | `{ project_id, workflow_id, input?, workflow_version?, idempotency_key? }` → run (201) |
| `GET` | `/runs` | Recent runs for the organization |
| `GET` | `/runs/{id}` | Run detail (status, input, output, error) |
| `POST` | `/runs/{id}/cancel` | 409 if already terminal |
| `GET` | `/runs/{id}/events` | Ordered lifecycle event history (persisted) |
| `GET` | `/runs/{id}/tasks` | Per-node task status and attempts |
| `WS` | `/ws/runs/{id}` | Live event stream (`{ "event": "...", "payload": {...} }`, `HEARTBEAT` keep-alive) |

The same operations are also available project-scoped under
`/projects/{pid}/workflows/{wid}/runs/...`.

### Approvals

| Method | Path | Notes |
| --- | --- | --- |
| `GET` | `/approvals` | Queue for the organization |
| `POST` | `/approvals/{id}/decision` | `{ decision: "approved" \| "rejected" }`; approved resumes the run, rejected fails it (approver/admin/owner) |

### Evaluations

| Method | Path | Notes |
| --- | --- | --- |
| `GET/POST` | `/projects/{pid}/evaluations` | `{ name, dataset: { cases: [...] }, threshold }` |
| `POST` | `/projects/{pid}/evaluations/{id}/run` | Scores every case; compares against the regression gate |
| `GET` | `/projects/{pid}/evaluations/{id}/runs` | Past evaluation runs |
| `GET` | `/projects/{pid}/evaluations/runs/{run_id}/cases` | Per-case results |
| `PUT` | `/projects/{pid}/evaluations/{id}/regression-gate` | `?baseline_score=&max_regression=&blocking=` |

### Memory

| Method | Path | Notes |
| --- | --- | --- |
| `POST` | `/projects/{pid}/memory` | `{ key, text, metadata }` — upsert (tenant+project scoped) |
| `POST` | `/projects/{pid}/memory/search` | `{ query, limit }` → ranked hits |

### Observability, reports, protocols

| Method | Path | Notes |
| --- | --- | --- |
| `GET` | `/dashboard`, `/reports/summary` | Organization rollups |
| `GET` | `/audit` | Append-only security events (most recent 200) |
| `GET` | `/version`, `/health/dependencies` | |
| `GET` | `/health/live`, `/health/ready`, `/metrics` | Unversioned; readiness pings Redis |
| `GET` | `/a2a/.well-known/agent-card.json` | A2A capability discovery |
| `POST` | `/a2a/tasks`, `GET /a2a/tasks/{id}` | Submit a task against a published workflow; poll status |
| `GET` | `/mcp/.well-known` | MCP discovery |
| `POST` | `/mcp` | JSON-RPC: `initialize`, `ping`, `tools/list`, `tools/call` (requires `project_id` + `agent_id`; high-risk tools are refused and must run via an approval-backed workflow) |
