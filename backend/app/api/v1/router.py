from fastapi import APIRouter

from app.api.v1.routes import (
    a2a,
    agents,
    approvals,
    audit,
    auth,
    dashboard,
    evaluations,
    mcp,
    memory,
    projects,
    reports,
    run_index,
    runs,
    system,
    team,
    tools,
    workflows,
)

api_router = APIRouter(prefix="/api/v1")

for module, tags in [
    (system.router, ["system"]),
    (auth.router, ["auth"]),
    (projects.router, ["projects"]),
    (agents.router, ["agents"]),
    (tools.router, ["tools"]),
    (workflows.router, ["workflows"]),
    (runs.router, ["runs"]),
    (run_index.router, ["runs"]),
    (approvals.router, ["approvals"]),
    (audit.router, ["audit"]),
    (evaluations.router, ["evaluations"]),
    (team.router, ["team"]),
    (dashboard.router, ["dashboard"]),
    (mcp.router, ["mcp"]),
    (a2a.router, ["a2a"]),
    (memory.router, ["memory"]),
    (reports.router, ["reports"]),
]:
    api_router.include_router(module, tags=tags)

# Compatibility alias: auth routes are also reachable under /api/v1/auth/*.
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
