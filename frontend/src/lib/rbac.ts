/** Front-end RBAC hints. The API remains the source of truth and re-checks every
 *  privileged operation; this only shapes what the UI offers. */

export type Role =
  | 'owner'
  | 'admin'
  | 'architect'
  | 'engineer'
  | 'operator'
  | 'approver'
  | 'auditor'
  | 'viewer';

export const ROLES: Role[] = [
  'owner',
  'admin',
  'architect',
  'engineer',
  'operator',
  'approver',
  'auditor',
  'viewer',
];

type Capability =
  | 'project.write'
  | 'agent.write'
  | 'tool.write'
  | 'workflow.write'
  | 'run.launch'
  | 'run.cancel'
  | 'approval.decide'
  | 'evaluation.write'
  | 'memory.write'
  | 'team.manage';

const MATRIX: Record<Capability, Role[]> = {
  'project.write': ['owner', 'admin', 'architect'],
  'agent.write': ['owner', 'admin', 'architect', 'engineer'],
  'tool.write': ['owner', 'admin', 'architect', 'engineer'],
  'workflow.write': ['owner', 'admin', 'architect', 'engineer'],
  'run.launch': ['owner', 'admin', 'architect', 'engineer', 'operator'],
  'run.cancel': ['owner', 'admin', 'operator'],
  'approval.decide': ['owner', 'admin', 'approver'],
  'evaluation.write': ['owner', 'admin', 'architect', 'engineer'],
  'memory.write': ['owner', 'admin', 'architect', 'engineer'],
  'team.manage': ['owner', 'admin'],
};

export function can(role: string | undefined, capability: Capability): boolean {
  if (!role) return false;
  return MATRIX[capability].includes(role as Role);
}
