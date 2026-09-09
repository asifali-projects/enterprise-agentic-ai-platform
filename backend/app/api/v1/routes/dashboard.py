from uuid import UUID

from fastapi import APIRouter
from sqlalchemy import func, select

from app.api.deps import Claims, Db
from app.db.models import Agent, Approval, AuditEvent, Project, Run, Tool, Workflow

router = APIRouter(prefix="/dashboard")


@router.get("")
async def dashboard(db: Db, c: Claims):
    org = UUID(c["org_id"])

    def q(model):
        return select(func.count()).select_from(model)

    project_ids = select(Project.id).where(Project.organization_id == org)
    values = {
        "projects": await db.scalar(q(Project).where(Project.organization_id == org)),
        "agents": await db.scalar(q(Agent).where(Agent.project_id.in_(project_ids))),
        "tools": await db.scalar(q(Tool).where(Tool.project_id.in_(project_ids))),
        "workflows": await db.scalar(q(Workflow).where(Workflow.project_id.in_(project_ids))),
        "runs": await db.scalar(q(Run).where(Run.project_id.in_(project_ids))),
        "approvals": await db.scalar(
            q(Approval).where(Approval.organization_id == org, Approval.status == "pending")
        ),
        "audit_events": await db.scalar(q(AuditEvent).where(AuditEvent.organization_id == org)),
    }
    return {"counts": values}
