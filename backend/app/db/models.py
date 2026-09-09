from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Identity,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, Timestamps, UUIDMixin


class Role(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    ARCHITECT = "architect"
    ENGINEER = "engineer"
    OPERATOR = "operator"
    APPROVER = "approver"
    AUDITOR = "auditor"
    VIEWER = "viewer"


class Status(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class RunStatus(StrEnum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"


class TaskStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"


class Risk(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Organization(UUIDMixin, Timestamps, Base):
    __tablename__ = "organizations"
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(220), unique=True, index=True, nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    demo_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class User(UUIDMixin, Timestamps, Base):
    __tablename__ = "users"
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(30), default=Role.VIEWER, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Invitation(UUIDMixin, Timestamps, Base):
    __tablename__ = "invitations"
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    email: Mapped[str] = mapped_column(String(320), index=True)
    role: Mapped[str] = mapped_column(String(30), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Project(UUIDMixin, Timestamps, Base):
    __tablename__ = "projects"
    __table_args__ = (UniqueConstraint("organization_id", "name", name="uq_project_org_name"),)
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default=Status.ACTIVE, nullable=False)


class Agent(UUIDMixin, Timestamps, Base):
    __tablename__ = "agents"
    __table_args__ = (UniqueConstraint("project_id", "name", name="uq_agent_project_name"),)
    project_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default=Status.DRAFT, nullable=False)


class AgentVersion(UUIDMixin, Timestamps, Base):
    __tablename__ = "agent_versions"
    __table_args__ = (UniqueConstraint("agent_id", "version", name="uq_agent_version"),)
    agent_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    model_provider: Mapped[str] = mapped_column(String(100), nullable=False)
    model_name: Mapped[str] = mapped_column(String(200), nullable=False)
    config: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class Tool(UUIDMixin, Timestamps, Base):
    __tablename__ = "tools"
    __table_args__ = (UniqueConstraint("project_id", "name", name="uq_tool_project_name"),)
    project_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), default=Risk.LOW, nullable=False)
    input_schema: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    endpoint: Mapped[str | None] = mapped_column(String(1000))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class ToolPermission(UUIDMixin, Timestamps, Base):
    __tablename__ = "tool_permissions"
    __table_args__ = (UniqueConstraint("agent_id", "tool_id", name="uq_agent_tool_permission"),)
    agent_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), index=True
    )
    tool_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tools.id", ondelete="CASCADE"), index=True
    )
    allowed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class Workflow(UUIDMixin, Timestamps, Base):
    __tablename__ = "workflows"
    __table_args__ = (UniqueConstraint("project_id", "name", name="uq_workflow_project_name"),)
    project_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default=Status.DRAFT, nullable=False)


class WorkflowVersion(UUIDMixin, Timestamps, Base):
    __tablename__ = "workflow_versions"
    __table_args__ = (UniqueConstraint("workflow_id", "version", name="uq_workflow_version"),)
    workflow_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("workflows.id", ondelete="CASCADE"), index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    definition: Mapped[dict] = mapped_column(JSON, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class Run(UUIDMixin, Timestamps, Base):
    __tablename__ = "runs"
    project_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    workflow_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("workflows.id", ondelete="RESTRICT"), index=True
    )
    workflow_version_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("workflow_versions.id", ondelete="RESTRICT")
    )
    status: Mapped[str] = mapped_column(String(30), default=RunStatus.PENDING, index=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(255), unique=True)
    input: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    output: Mapped[dict | None] = mapped_column(JSON)
    error: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class RunTask(UUIDMixin, Timestamps, Base):
    __tablename__ = "run_tasks"
    run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("runs.id", ondelete="CASCADE"), index=True
    )
    task_id: Mapped[str] = mapped_column(String(200), nullable=False)
    agent_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("agents.id"))
    status: Mapped[str] = mapped_column(String(30), default=TaskStatus.PENDING)
    input: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    output: Mapped[dict | None] = mapped_column(JSON)
    error: Mapped[str | None] = mapped_column(Text)
    attempt: Mapped[int] = mapped_column(Integer, default=0)


class RunEvent(UUIDMixin, Base):
    __tablename__ = "run_events"
    seq: Mapped[int] = mapped_column(BigInteger, Identity(), nullable=False, unique=True)
    run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("runs.id", ondelete="CASCADE"), index=True
    )
    event: Mapped[str] = mapped_column(String(50), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Approval(UUIDMixin, Base):
    __tablename__ = "approvals"
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("runs.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[str] = mapped_column(String(20), default="pending")
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    decided_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AuditEvent(UUIDMixin, Base):
    __tablename__ = "audit_events"
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    actor_user_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), index=True)
    action: Mapped[str] = mapped_column(String(200), index=True)
    resource_type: Mapped[str] = mapped_column(String(100))
    resource_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    event_metadata: Mapped[dict] = mapped_column("metadata", JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Evaluation(UUIDMixin, Timestamps, Base):
    __tablename__ = "evaluations"
    project_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    dataset: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    threshold: Mapped[float] = mapped_column(default=0.8)
    last_score: Mapped[float | None] = mapped_column()


class EvaluationRun(UUIDMixin, Timestamps, Base):
    __tablename__ = "evaluation_runs"
    evaluation_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("evaluations.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[str] = mapped_column(String(30), default="running", nullable=False, index=True)
    score: Mapped[float | None] = mapped_column()
    passed: Mapped[bool | None] = mapped_column(Boolean)
    baseline_score: Mapped[float | None] = mapped_column()
    regression_delta: Mapped[float | None] = mapped_column()
    error: Mapped[str | None] = mapped_column(Text)


class EvaluationCaseResult(UUIDMixin, Timestamps, Base):
    __tablename__ = "evaluation_case_results"
    evaluation_run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("evaluation_runs.id", ondelete="CASCADE"), index=True
    )
    case_index: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[float] = mapped_column(nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    expected: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    actual: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    error: Mapped[str | None] = mapped_column(Text)


class RegressionGate(UUIDMixin, Timestamps, Base):
    __tablename__ = "regression_gates"
    evaluation_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("evaluations.id", ondelete="CASCADE"), index=True
    )
    baseline_score: Mapped[float] = mapped_column(nullable=False)
    max_regression: Mapped[float] = mapped_column(default=0.05, nullable=False)
    blocking: Mapped[bool] = mapped_column(default=True, nullable=False)
