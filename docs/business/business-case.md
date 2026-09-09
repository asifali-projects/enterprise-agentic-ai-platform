# Business case

## Summary

Enterprises are moving from AI pilots to AI in production. The blocker is not
model capability — it is operational control. The Enterprise Agentic AI
Operating Platform is the system of record and control plane for running AI
agents safely: least-privilege tool access, human approval for high-impact
actions, reliable execution, evaluation gates, full audit, and tenant isolation.

## Market problem

Organizations that have built agent prototypes consistently stall at the same
point: security, compliance and platform teams will not let an agent touch
production systems without controls that the prototype does not have. Teams then
either (a) build a bespoke control layer per project, duplicating effort and
inconsistently, or (b) do not ship. Both outcomes waste the investment already
made in the agents themselves.

## Value proposition

| Buyer concern | What the platform provides | Business outcome |
| --- | --- | --- |
| "Can an agent do something it shouldn't?" | Default-deny tool gateway, per-agent permissions, outbound host allowlist | Reduced risk of unintended or unauthorized actions |
| "Who signed off on this?" | Human approval gates with actor + timestamp; append-only audit trail | Demonstrable oversight for audit and compliance |
| "Will it break in production?" | State machine, timeouts, bounded concurrency, idempotency, safe retries | Fewer incidents; predictable behavior |
| "Did our last change make it worse?" | Evaluations with regression gates tied to agent versions | Quality does not silently degrade across releases |
| "Can we see what happened?" | Correlation IDs, structured logs, traces, live + persisted run events | Faster incident resolution; lower operating cost |
| "Is customer A isolated from customer B?" | Organization-scoped data, permissions and vector namespaces | Enables multi-team and multi-customer deployments |
| "Are we locked into one model vendor?" | Mandatory provider abstraction (local + OpenAI-compatible) | Negotiating leverage; portability |

The core pitch: **one platform replaces the per-project control layer** that
teams would otherwise rebuild, and turns "we have agents" into "we operate
agents".

## Target customers

- **Primary:** mid-to-large enterprises with an internal platform/ML team, a
  security function, and multiple business units wanting to adopt agents.
- **Secondary:** software vendors embedding agentic features who need governance
  and multi-tenancy they do not want to build.
- **Buyer:** Head of AI Platform / Director of ML Engineering, co-signed by
  Security and Compliance.
- **Users:** AI/ML engineers, AI architects, platform engineers, operations and
  approvers.

## Positioning

- **vs. agent frameworks (build-your-own orchestration):** those help you build
  an agent; this operates a fleet — permissions, approvals, audit, evaluation,
  multi-tenancy are the product, not an exercise for the reader.
- **vs. observability-only tools:** tracing tells you what happened; this also
  enforces what is allowed to happen and gates releases on quality.
- **vs. a single-vendor agent platform:** provider-neutral by design; the LLM is
  configuration, not a lock-in.

## Business / commercial model (illustrative)

- **Deployment:** customer-hosted (Docker Compose for evaluation, Kubernetes for
  production) or managed.
- **Pricing dimensions:** per tenant/organization, per active agent version, and
  per run volume, with an enterprise tier for SSO, custom retention and support.
- **Land:** a single team runs one workflow through approval and evaluation.
- **Expand:** more projects, more business units onboarded, more of the run
  volume governed through the platform.

## Success metrics

| Metric | Why it matters |
| --- | --- |
| Time from "agent works locally" to "agent runs in production with approval + audit" | Core value: shrink this from months to days |
| % of agent runs executed through the governed platform (vs. ungoverned scripts) | Adoption / risk-reduction proxy |
| Number of high-impact actions caught at the approval gate | Demonstrated control value |
| Evaluation-gate blocks per quarter | Prevented regressions |
| Mean time to explain an incident ("who/what/when") | Operating-cost reduction |
| Projects and business units onboarded per account | Expansion |

## Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| "Our framework already does orchestration" | Position on the governance/operations layer, not orchestration; integrate rather than replace via MCP/A2A |
| Model/provider churn | Provider abstraction is mandatory; adapters are small |
| Perceived heavyweight for small teams | Guided demo tenant and Docker Compose one-command start lower the trial cost |
| Unproven at scale | Concurrency is bounded and the design is horizontal; publish benchmarks before making scale claims |
