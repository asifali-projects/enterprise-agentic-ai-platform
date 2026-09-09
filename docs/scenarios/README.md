# Test & demo scenarios

All scenarios are designed for authorized, synthetic, local environments. The
platform's security-assessment features require explicit authorization and use
synthetic/local demo targets only.

| ID | Scenario | Controls exercised | Where |
| --- | --- | --- | --- |
| AG-001 | Customer-support resolution workflow | triage → knowledge → policy → approved action; workflow reaches a terminal state and records tool decisions | Demo tenant workflow "Support Resolution"; `services/execution.py` |
| AG-002 | Multi-agent research workflow | planner delegates to child agents; all children complete or fail explicitly | DAG with `depends_on`; `services/execution.py` fan-out |
| AG-003 | Unauthorized tool request | gateway rejects a tool call outside the agent's scope **before** execution; denial is recorded | `services/execution.py` (`ToolPermission` check), MCP `tools/call` |
| AG-004 | Human approval gate | high-risk tool node pauses the run, emits `APPROVAL_REQUIRED`, resumes only on an authorized approval; rejection fails the run | `services/execution.py`, `api/v1/routes/approvals.py` |
| AG-005 | Worker timeout / recovery | long task hits `RUN_TIMEOUT_SECONDS`, run → `TIMED_OUT`; idempotency key makes a safe retry produce one outcome | `services/execution.py`, `services/runs.py` (idempotency) |
| AG-006 | Prompt/context regression | evaluation run scores below the regression gate's allowed margin and is flagged / blocked | `services/evaluation.py` (`RegressionGate`) |
| AG-007 | Concurrent tenant isolation | two organizations run workflows concurrently; no cross-tenant records, vectors or permissions are visible | organization-scoped queries; `test_workflow_and_runs.py::test_cross_tenant_project_access_is_blocked` |
| AG-008 | Agent failure cascade | one child task fails; the parent run marks failure and follows its fallback path without corrupting state | `services/execution.py` (exception propagation, terminal transition) |

## Automated coverage

| Test | Scenario(s) |
| --- | --- |
| `test_validation.py` | AG-002 (graph correctness), AG-008 (deadlock guard) |
| `test_workflow_and_runs.py::test_workflow_rejects_dependency_cycle` | AG-002 |
| `test_workflow_and_runs.py::test_run_lifecycle_and_events` | AG-001, AG-005 (lifecycle + persisted events) |
| `test_workflow_and_runs.py::test_run_without_published_version_is_rejected` | AG-001 (explicit failure) |
| `test_workflow_and_runs.py::test_cross_tenant_project_access_is_blocked` | AG-007 |
| `test_auth_flow.py` | RBAC, invitation authorization |
| `test_protocols.py` | AG-006 (scoring function) |
| `test_protocol_contracts.py` | MCP / A2A contract surface |

## Manual demo script

See [../product/overview.md#first-journey-demo-walkthrough](../product/overview.md#first-journey-demo-walkthrough)
for the end-to-end click path (create org → project → agent → tool → workflow →
run → approve → evaluate → audit).
