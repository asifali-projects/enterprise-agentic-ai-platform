# Documentation

The Enterprise Agentic AI Operating Platform is a production-oriented control
plane for building, orchestrating and operating enterprise AI agents and
multi-agent workflows.

## Map

| Area | Document | Audience |
| --- | --- | --- |
| **Product** | [product/overview.md](product/overview.md) | Product, leadership, prospective users |
| | [product/requirements.md](product/requirements.md) | Product, engineering |
| **Business** | [business/business-case.md](business/business-case.md) | Leadership, sales, investors |
| **Technical** | [technical/architecture.md](technical/architecture.md) | Engineering, architects |
| | [technical/backend.md](technical/backend.md) | Backend engineers |
| | [technical/frontend.md](technical/frontend.md) | Frontend engineers |
| | [technical/api.md](technical/api.md) | Integrators, frontend, partners |
| | [technical/operations.md](technical/operations.md) | Platform / SRE |
| **Scenarios** | [scenarios/README.md](scenarios/README.md) | QA, security, engineering |

## One-paragraph summary

Teams can prototype AI agents quickly but struggle to run them in production:
tool permissions, memory, human approvals, reliability, evaluation,
observability and auditability all have to be solved before an agent can be
trusted with real work. This platform provides those controls as a single,
tenant-isolated system with a typed API, a React control plane, a durable run
queue with bounded parallel execution, a default-deny tool gateway, human
approval gates, reproducible evaluations with regression gates, and a complete
audit trail — deployable locally with Docker Compose and ready for Kubernetes.

## Quick links

- Local setup and demo walkthrough: [../README.md](../README.md)
- API reference: [technical/api.md](technical/api.md)
- Environment variables: [technical/operations.md#configuration](technical/operations.md#configuration)
- Known limitations: [technical/operations.md#known-limitations](technical/operations.md#known-limitations)
