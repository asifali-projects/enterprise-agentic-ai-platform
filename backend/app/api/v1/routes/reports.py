from uuid import UUID

from fastapi import APIRouter
from sqlalchemy import func, select

from app.api.deps import Claims, Db
from app.db.models import Agent, AuditEvent, Evaluation, Project, Run, Tool, Workflow

router = APIRouter(prefix="/reports")


@router.get("/summary")
async def summary(db: Db, c: Claims):
    org = UUID(c["org_id"])

    async def count(model, field=None):
        q = select(func.count()).select_from(model)
        if field is not None:
            q = q.where(field == org)
        return int(await db.scalar(q) or 0)

    project_ids = select(Project.id).where(Project.organization_id == org)
    return {
        "organization_id": str(org),
        "projects": await count(Project, Project.organization_id),
        "agents": int(
            await db.scalar(
                select(func.count()).select_from(Agent).where(Agent.project_id.in_(project_ids))
            )
            or 0
        ),
        "tools": int(
            await db.scalar(
                select(func.count()).select_from(Tool).where(Tool.project_id.in_(project_ids))
            )
            or 0
        ),
        "workflows": int(
            await db.scalar(
                select(func.count())
                .select_from(Workflow)
                .where(Workflow.project_id.in_(project_ids))
            )
            or 0
        ),
        "runs": int(
            await db.scalar(
                select(func.count()).select_from(Run).where(Run.project_id.in_(project_ids))
            )
            or 0
        ),
        "audit_events": await count(AuditEvent, AuditEvent.organization_id),
        "evaluations": int(
            await db.scalar(
                select(func.count())
                .select_from(Evaluation)
                .where(Evaluation.project_id.in_(project_ids))
            )
            or 0
        ),
    }
