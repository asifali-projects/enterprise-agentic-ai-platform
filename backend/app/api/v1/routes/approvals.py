from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.api.deps import Claims, Db
from app.db.models import Approval, Run, RunStatus
from app.schemas.api import ApprovalDecision
from app.services.events import publish
from app.services.queue import enqueue_run

router = APIRouter(prefix="/approvals")


@router.get("")
async def listing(db: Db, c: Claims):
    return list(
        (
            await db.execute(
                select(Approval)
                .where(Approval.organization_id == UUID(c["org_id"]))
                .order_by(Approval.decided_at.asc().nullsfirst())
            )
        ).scalars()
    )


@router.post("/{approval_id}/decision")
async def decide(approval_id: UUID, data: ApprovalDecision, db: Db, c: Claims):
    x = await db.scalar(
        select(Approval).where(
            Approval.id == approval_id, Approval.organization_id == UUID(c["org_id"])
        )
    )
    if not x:
        raise HTTPException(404, "Approval not found")
    if x.status != "pending":
        raise HTTPException(409, "Approval already decided")
    run = await db.scalar(select(Run).where(Run.id == x.run_id))
    if not run:
        raise HTTPException(404, "Run not found")
    x.status = data.decision
    x.decided_by = UUID(c["sub"])
    x.decided_at = datetime.now(UTC)
    if data.decision == "rejected":
        run.status = RunStatus.FAILED
        run.error = "Human approval rejected"
    else:
        run.status = RunStatus.QUEUED
    await db.commit()
    await publish(run.id, "APPROVAL_DECIDED", {"decision": data.decision, "approval_id": str(x.id)})
    if data.decision == "approved":
        await enqueue_run(run.id)
    return {"id": x.id, "status": x.status, "run_id": run.id}
