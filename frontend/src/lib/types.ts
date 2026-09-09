export interface Project {
  id: string;
  organization_id: string;
  name: string;
  description: string | null;
  status: string;
}

export interface Agent {
  id: string;
  project_id: string;
  name: string;
  description: string | null;
  status: string;
}

export interface AgentVersion {
  id: string;
  agent_id: string;
  version: number;
  system_prompt: string;
  model_provider: string;
  model_name: string;
  is_published: boolean;
}

export interface Tool {
  id: string;
  project_id: string;
  name: string;
  description: string;
  risk_level: string;
  enabled: boolean;
  endpoint: string | null;
}

export interface Workflow {
  id: string;
  project_id: string;
  name: string;
  description: string | null;
  status: string;
}

export interface WorkflowVersion {
  id: string;
  workflow_id: string;
  version: number;
  is_published: boolean;
}

export interface Run {
  id: string;
  project_id: string;
  workflow_id: string;
  status: string;
  idempotency_key: string | null;
  input: Record<string, unknown>;
  output: Record<string, unknown> | null;
  error: string | null;
  created_at?: string;
}

export interface RunEvent {
  event: string;
  payload: Record<string, unknown>;
  created_at: string;
}

export interface RunTask {
  id: string;
  task_id: string;
  status: string;
  attempt: number;
  error: string | null;
}

export interface Approval {
  id: string;
  status: string;
  reason: string;
  run_id: string;
  decided_at: string | null;
}

export interface Evaluation {
  id: string;
  project_id: string;
  name: string;
  threshold: number;
  last_score: number | null;
}

export interface EvaluationRun {
  id: string;
  status: string;
  score: number | null;
  passed: boolean | null;
  regression_delta: number | null;
  created_at?: string;
}

export interface AuditEvent {
  id: string;
  action: string;
  resource_type: string;
  actor_user_id: string | null;
  created_at: string;
}

export interface TeamMember {
  id: string;
  full_name: string;
  email: string;
  role: string;
  is_active: boolean;
}

export interface DashboardCounts {
  projects: number;
  agents: number;
  tools: number;
  workflows: number;
  runs: number;
  approvals: number;
  audit_events: number;
}
