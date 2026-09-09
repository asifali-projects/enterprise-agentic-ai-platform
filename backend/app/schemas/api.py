from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Node(BaseModel):
    id: str = Field(min_length=1, max_length=200)
    type: str = "agent"
    agent_id: UUID | None = None
    tool_id: UUID | None = None
    input: dict = {}
    depends_on: list[str] = []


class Definition(BaseModel):
    nodes: list[Node] = []
    max_concurrency: int | None = Field(default=None, ge=1, le=64)


class Register(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=200)
    password: str = Field(min_length=12, max_length=128)
    organization_name: str = Field(min_length=2, max_length=200)


class Login(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class InviteIn(BaseModel):
    email: EmailStr
    role: str


class DemoIn(BaseModel):
    organization_name: str = "Demo Organization"
    full_name: str = "Demo User"
    email: EmailStr | None = None


class ProjectCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    description: str | None = None


class ProjectOut(ORM):
    id: UUID
    organization_id: UUID
    name: str
    description: str | None
    status: str


class AgentCreate(BaseModel):
    name: str
    description: str | None = None


class AgentOut(ORM):
    id: UUID
    project_id: UUID
    name: str
    description: str | None
    status: str


class AgentVersionCreate(BaseModel):
    system_prompt: str
    model_provider: str = "local"
    model_name: str = "deterministic"
    config: dict = {}


class AgentVersionOut(ORM):
    id: UUID
    agent_id: UUID
    version: int
    system_prompt: str
    model_provider: str
    model_name: str
    config: dict
    is_published: bool


class ToolCreate(BaseModel):
    name: str
    description: str
    risk_level: str = "low"
    input_schema: dict = {}
    endpoint: str | None = None


class ToolOut(ORM):
    id: UUID
    project_id: UUID
    name: str
    description: str
    risk_level: str
    input_schema: dict
    endpoint: str | None
    enabled: bool


class Permission(BaseModel):
    tool_id: UUID
    allowed: bool


class WorkflowCreate(BaseModel):
    name: str
    description: str | None = None


class WorkflowOut(ORM):
    id: UUID
    project_id: UUID
    name: str
    description: str | None
    status: str


class WorkflowVersionCreate(BaseModel):
    definition: dict


class WorkflowVersionOut(ORM):
    id: UUID
    workflow_id: UUID
    version: int
    definition: dict
    is_published: bool


class RunCreate(BaseModel):
    input: dict = {}
    workflow_version: int | None = None
    idempotency_key: str | None = None


class RunSubmit(BaseModel):
    project_id: UUID
    workflow_id: UUID
    input: dict = {}
    workflow_version: int | None = None
    idempotency_key: str | None = None


class RunOut(ORM):
    id: UUID
    project_id: UUID
    workflow_id: UUID
    workflow_version_id: UUID
    status: str
    idempotency_key: str | None
    input: dict
    output: dict | None
    error: str | None


class ApprovalDecision(BaseModel):
    decision: str = Field(pattern="^(approved|rejected)$")


class EvaluationCreate(BaseModel):
    name: str
    dataset: dict = {}
    threshold: float = Field(default=0.8, ge=0, le=1)


class EvaluationOut(ORM):
    id: UUID
    project_id: UUID
    name: str
    dataset: dict
    threshold: float
    last_score: float | None
