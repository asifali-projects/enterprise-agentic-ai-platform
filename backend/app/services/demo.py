from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.db.models import (
    Agent,
    AgentVersion,
    Organization,
    Project,
    Role,
    Tool,
    ToolPermission,
    User,
    Workflow,
    WorkflowVersion,
)
from app.schemas.api import DemoIn


async def provision_demo(db: AsyncSession, data: DemoIn) -> str:
    slug = "demo-" + uuid4().hex[:10]
    org = Organization(
        name=data.organization_name,
        slug=slug,
        is_demo=True,
        demo_expires_at=datetime.now(UTC) + timedelta(minutes=settings.demo_ttl_minutes),
    )
    db.add(org)
    await db.flush()
    email = data.email or f"demo-{uuid4().hex[:8]}@example.local"
    user = User(
        organization_id=org.id,
        email=email.lower(),
        full_name=data.full_name,
        password_hash=hash_password(uuid4().hex + "A!9"),
        role=Role.ADMIN,
    )
    db.add(user)
    project = Project(
        organization_id=org.id,
        name="Customer Support Demo",
        description="Safe synthetic demo project",
    )
    db.add(project)
    await db.flush()
    agent = Agent(
        project_id=project.id, name="Customer Support Agent", description="Synthetic support agent"
    )
    db.add(agent)
    await db.flush()
    av = AgentVersion(
        agent_id=agent.id,
        version=1,
        system_prompt="Answer synthetic support requests safely.",
        model_provider="local",
        model_name="deterministic",
        is_published=True,
    )
    db.add(av)
    tool = Tool(
        project_id=project.id,
        name="Knowledge Search",
        description="Synthetic read-only knowledge lookup",
    )
    db.add(tool)
    await db.flush()
    db.add(ToolPermission(agent_id=agent.id, tool_id=tool.id, allowed=True))
    wf = Workflow(
        project_id=project.id,
        name="Support Resolution Demo",
        description="Triage → knowledge → response",
    )
    db.add(wf)
    await db.flush()
    db.add(
        WorkflowVersion(
            workflow_id=wf.id,
            version=1,
            definition={
                "nodes": [
                    {"id": "triage", "type": "agent", "agent_id": str(agent.id)},
                    {
                        "id": "response",
                        "type": "agent",
                        "agent_id": str(agent.id),
                        "depends_on": ["triage"],
                    },
                ],
                "max_concurrency": 2,
            },
            is_published=True,
        )
    )
    await db.commit()
    return create_access_token(str(user.id), str(org.id), user.role)
