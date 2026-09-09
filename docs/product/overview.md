# Product overview

## Vision

Give enterprises a single control plane to take AI agents from prototype to
production — with the governance, reliability and auditability that regulated
organizations require before an agent is allowed to act on real systems.

## The problem

Building an agent that works in a notebook is easy. Operating a fleet of agents
that other teams depend on is not. The gaps that stall production adoption:

| Gap | Consequence without a platform |
| --- | --- |
| Tool permissions | Agents can call anything the process can reach; no least-privilege story |
| Human oversight | No safe way to require sign-off before a high-impact action |
| Reliability | Long-running agent tasks hang, retry unsafely, or duplicate side effects |
| Memory | Ad-hoc vector stores with no tenant isolation |
| Evaluation | No baseline, so prompt/model changes silently regress quality |
| Observability | No correlation between a user request, an agent run and a provider call |
| Auditability | No answer to "who approved this and when" |
| Multi-tenancy | One customer's data and permissions leak into another's |

## What this product is

A production-oriented platform with clear separation between UI, API,
orchestration, data, AI-provider abstraction and infrastructure. It ships with:

- **Authentication & RBAC** — 8 roles from `owner` to `viewer`; every privileged
  operation is authorized server-side.
- **Organizations & projects** — hard tenant isolation; projects scope agents,
  tools, workflows and memory.
- **Agent registry** — agents with immutable version records and an explicit
  publish step.
- **Tool registry & gateway** — risk-tiered tools, per-agent permissions,
  default-deny authorization enforced before execution, outbound host
  allowlisting.
- **Workflow builder** — DAG workflows validated for unique ids, resolvable
  dependencies and acyclicity; versioned and published.
- **Run orchestrator & workers** — durable queue, bounded parallel execution,
  per-task timeout, cancellation, idempotency keys, safe retries.
- **Human approval gates** — high-risk tool actions pause the run and wait for
  an authorized decision; model output can never release the gate.
- **Evaluations & regression gates** — score agent versions against a fixed
  dataset; block releases that regress beyond an allowed margin.
- **Memory service** — tenant/project-scoped vector storage and semantic search.
- **Observability** — correlation IDs, structured JSON logs, OpenTelemetry
  traces/metrics, Prometheus endpoint, live run-event streaming.
- **Audit trail** — append-only record of security-relevant events.
- **Protocols** — a governed MCP JSON-RPC gateway and an A2A-compatible agent
  card and task contract for interoperating with external agents.

## Personas

| Persona | Uses the platform to… |
| --- | --- |
| **AI/ML engineer** | Register agents, iterate on prompts/versions, run evaluations |
| **AI architect** | Compose multi-agent workflows, set tool permissions and approval policy |
| **Platform engineer** | Deploy and operate the stack, wire providers and telemetry |
| **Operations / admin** | Manage the team and roles, watch runs, hold the audit trail |
| **Approver** | Review and decide high-impact actions paused at the approval gate |
| **Auditor** | Read the immutable event history |

## First journey (demo walkthrough)

1. Create an organization (or open the guided demo tenant).
2. Create a project.
3. Register an agent, add a version, publish it.
4. Register a tool; grant it to the agent (default is deny).
5. Compose a workflow (a small DAG), add a version, publish it.
6. Launch a run from the Runs page; watch lifecycle events stream in.
7. If a node uses a high-risk tool, approve it from the Approvals queue; the run
   resumes.
8. Create an evaluation dataset, run it, attach a regression gate.
9. Inspect the run's tasks, events and the audit trail.
10. Integrate an external agent via A2A, or expose governed tools over MCP.

## Definition of done — status

| Capability | Status |
| --- | --- |
| Create an agent and version it | ✅ |
| Compose a workflow with bounded parallel tasks | ✅ |
| Enforce tool-level authorization before execution | ✅ |
| Pause/resume high-impact workflows via approval | ✅ |
| Stream live run state over WebSockets | ✅ (+ persisted history) |
| Persist complete run/audit history | ✅ |
| Run evaluation datasets and compare versions | ✅ |
| Deploy locally with Docker; document Kubernetes | ✅ |
| README with setup, architecture, env vars, demo, tests, deployment, limitations | ✅ |

## Roadmap (near-term)

- Real embedding adapter for the memory service.
- Semantic evaluation scorers in addition to field-match.
- In-UI workflow graph editor (today the definition is edited as JSON).
- Per-module `mypy --strict` restoration.
- Published load/latency benchmarks.
