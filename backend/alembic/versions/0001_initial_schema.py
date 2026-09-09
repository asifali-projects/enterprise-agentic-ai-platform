"""Consolidated initial schema.

This is the single baseline migration for the platform. It materialises every
table defined by the SQLAlchemy models (users, organizations, projects, agents,
agent_versions, tools, tool_permissions, workflows, workflow_versions, runs,
run_tasks, run_events, approvals, audit_events, invitations, evaluations,
evaluation_runs, evaluation_case_results, regression_gates).

Subsequent schema changes should be added as further Alembic revisions produced
with ``alembic revision --autogenerate``.
"""

from alembic import op

from app.db.base import Base
from app.db import models  # noqa: F401  (import registers every model on Base.metadata)

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
