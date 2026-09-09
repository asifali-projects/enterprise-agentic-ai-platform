from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    AgentVersion,
    Evaluation,
    EvaluationCaseResult,
    EvaluationRun,
    RegressionGate,
)
from app.services.llm import provider


async def run_evaluation(db: AsyncSession, evaluation_id: UUID) -> EvaluationRun:
    evaluation = await db.scalar(select(Evaluation).where(Evaluation.id == evaluation_id))
    if not evaluation:
        raise ValueError("Evaluation not found")
    run = EvaluationRun(evaluation_id=evaluation.id, status="running")
    db.add(run)
    await db.flush()
    cases = evaluation.dataset.get("cases", []) if isinstance(evaluation.dataset, dict) else []
    scores = []
    try:
        for i, case in enumerate(cases):
            case = case if isinstance(case, dict) else {"input": {"value": case}}
            expected = (
                case.get("expected", {})
                if isinstance(case.get("expected", {}), dict)
                else {"value": case.get("expected")}
            )
            actual = case.get("actual")
            try:
                if actual is None:
                    agent_id = case.get("agent_id")
                    if not agent_id:
                        raise ValueError("Each evaluation case needs actual or agent_id")
                    av = await db.scalar(
                        select(AgentVersion).where(
                            AgentVersion.agent_id == UUID(str(agent_id)),
                            AgentVersion.is_published.is_(True),
                        )
                    )
                    if not av:
                        raise ValueError("Published agent version not found")
                    actual = await provider().generate(av.system_prompt, case.get("input", {}))
                score = score_case(expected, actual)
                passed = score >= evaluation.threshold
                db.add(
                    EvaluationCaseResult(
                        evaluation_run_id=run.id,
                        case_index=i,
                        score=score,
                        passed=passed,
                        expected=expected,
                        actual=actual if isinstance(actual, dict) else {"value": actual},
                    )
                )
                scores.append(score)
            except Exception as exc:
                db.add(
                    EvaluationCaseResult(
                        evaluation_run_id=run.id,
                        case_index=i,
                        score=0,
                        passed=False,
                        expected=expected,
                        actual={},
                        error=str(exc),
                    )
                )
                scores.append(0)
        run.score = sum(scores) / len(scores) if scores else 0.0
        gate = await db.scalar(
            select(RegressionGate).where(RegressionGate.evaluation_id == evaluation.id)
        )
        if gate:
            run.baseline_score = gate.baseline_score
            run.regression_delta = run.score - gate.baseline_score
            regression_ok = run.regression_delta >= -gate.max_regression
        else:
            regression_ok = True
        run.passed = bool(scores) and run.score >= evaluation.threshold and regression_ok
        run.status = "succeeded"
        evaluation.last_score = run.score
        await db.commit()
        await db.refresh(run)
        return run
    except Exception as exc:
        run.status = "failed"
        run.error = str(exc)
        await db.commit()
        raise


def score_case(expected: dict, actual: dict) -> float:
    if expected == actual:
        return 1.0
    if not expected:
        return 0.0
    matches = 0
    for key, value in expected.items():
        if key in actual and actual[key] == value:
            matches += 1
    return matches / len(expected)
