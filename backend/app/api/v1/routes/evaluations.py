from uuid import UUID

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.api.deps import Db, ProjectDep
from app.db.models import Evaluation, EvaluationCaseResult, EvaluationRun, RegressionGate
from app.schemas.api import EvaluationCreate, EvaluationOut
from app.services.evaluation import run_evaluation

router = APIRouter(prefix="/projects/{project_id}/evaluations")


@router.post("", response_model=EvaluationOut)
async def create(data: EvaluationCreate, p=ProjectDep, db: Db = None):
    x = Evaluation(project_id=p.id, name=data.name, dataset=data.dataset, threshold=data.threshold)
    db.add(x)
    await db.commit()
    await db.refresh(x)
    return x


@router.get("", response_model=list[EvaluationOut])
async def listing(p=ProjectDep, db: Db = None):
    return list(
        (
            await db.execute(
                select(Evaluation)
                .where(Evaluation.project_id == p.id)
                .order_by(Evaluation.created_at.desc())
            )
        ).scalars()
    )


@router.post("/{evaluation_id}/run")
async def execute(evaluation_id: UUID, p=ProjectDep, db: Db = None):
    evaluation = await db.scalar(
        select(Evaluation).where(Evaluation.id == evaluation_id, Evaluation.project_id == p.id)
    )
    if not evaluation:
        raise HTTPException(404, "Evaluation not found")
    run = await run_evaluation(db, evaluation.id)
    return {
        "id": str(run.id),
        "status": run.status,
        "score": run.score,
        "passed": run.passed,
        "baseline_score": run.baseline_score,
        "regression_delta": run.regression_delta,
    }


@router.get("/{evaluation_id}/runs")
async def runs(evaluation_id: UUID, p=ProjectDep, db: Db = None):
    e = await db.scalar(
        select(Evaluation).where(Evaluation.id == evaluation_id, Evaluation.project_id == p.id)
    )
    if not e:
        raise HTTPException(404, "Evaluation not found")
    return list(
        (
            await db.execute(
                select(EvaluationRun)
                .where(EvaluationRun.evaluation_id == e.id)
                .order_by(EvaluationRun.created_at.desc())
            )
        ).scalars()
    )


@router.put("/{evaluation_id}/regression-gate")
async def gate(
    evaluation_id: UUID,
    baseline_score: float,
    max_regression: float = 0.05,
    blocking: bool = True,
    p=ProjectDep,
    db: Db = None,
):
    if not 0 <= baseline_score <= 1 or not 0 <= max_regression <= 1:
        raise HTTPException(422, "Scores must be between 0 and 1")
    e = await db.scalar(
        select(Evaluation).where(Evaluation.id == evaluation_id, Evaluation.project_id == p.id)
    )
    if not e:
        raise HTTPException(404, "Evaluation not found")
    g = await db.scalar(select(RegressionGate).where(RegressionGate.evaluation_id == e.id))
    if not g:
        g = RegressionGate(
            evaluation_id=e.id,
            baseline_score=baseline_score,
            max_regression=max_regression,
            blocking=blocking,
        )
        db.add(g)
    else:
        g.baseline_score = baseline_score
        g.max_regression = max_regression
        g.blocking = blocking
    await db.commit()
    return {
        "evaluation_id": str(e.id),
        "baseline_score": baseline_score,
        "max_regression": max_regression,
        "blocking": blocking,
    }


@router.get("/runs/{run_id}/cases")
async def cases(run_id: UUID, p=ProjectDep, db: Db = None):
    e = await db.scalar(
        select(Evaluation)
        .join(EvaluationRun, EvaluationRun.evaluation_id == Evaluation.id)
        .where(EvaluationRun.id == run_id, Evaluation.project_id == p.id)
    )
    if not e:
        raise HTTPException(404, "Evaluation run not found")
    return list(
        (
            await db.execute(
                select(EvaluationCaseResult)
                .where(EvaluationCaseResult.evaluation_run_id == run_id)
                .order_by(EvaluationCaseResult.case_index)
            )
        ).scalars()
    )
