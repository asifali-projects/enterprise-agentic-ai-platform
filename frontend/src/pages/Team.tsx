import { useState } from 'react';
import { ApiError } from '../lib/api';
import { useAuth } from '../lib/auth';
import { can, ROLES } from '../lib/rbac';
import { useMutation, useQuery } from '../lib/useApi';
import { useToast } from '../components/Toast';
import {
  Button,
  DataTable,
  EmptyState,
  ErrorState,
  Field,
  LoadingBlock,
  Panel,
  SelectField,
  StatusBadge,
} from '../components/ui';
import type { TeamMember } from '../lib/types';
import { email as emailRule } from '../lib/validation';
import { titleCase } from '../lib/format';

export function Team() {
  const { user } = useAuth();
  const toast = useToast();
  const manager = can(user?.role, 'team.manage');
  const { data, error, loading, reload } = useQuery<TeamMember[]>('/api/v1/team/users');
  const { mutate, pending } = useMutation();

  const [inviteEmail, setInviteEmail] = useState('');
  const [role, setRole] = useState('viewer');
  const [emailError, setEmailError] = useState<string | null>(null);

  async function invite() {
    const validation = emailRule(inviteEmail);
    if (validation) {
      setEmailError(validation);
      return;
    }
    setEmailError(null);
    try {
      const result = await mutate<{ token: string }>('/api/v1/team/invite', {
        method: 'POST',
        body: { email: inviteEmail.trim(), role },
      });
      toast.success(
        'Invitation created',
        `Share this one-time token with ${inviteEmail.trim()}: ${result.token}`,
      );
      setInviteEmail('');
    } catch (err) {
      toast.error('Could not create invitation', err instanceof ApiError ? err.message : undefined);
    }
  }

  if (!manager) {
    return (
      <div className="page">
        <EmptyState
          title="Administrator access required"
          description="Only organization owners and admins can manage team members and roles."
        />
      </div>
    );
  }

  return (
    <div className="page">
      <Panel eyebrow="Invite" title="Add a team member">
        <div className="inline-form">
          <Field
            label="Work email"
            type="email"
            value={inviteEmail}
            error={emailError}
            onChange={(e) => setInviteEmail(e.target.value)}
          />
          <SelectField label="Role" value={role} onChange={(e) => setRole(e.target.value)}>
            {ROLES.map((value) => (
              <option key={value} value={value}>
                {titleCase(value)}
              </option>
            ))}
          </SelectField>
          <Button variant="primary" loading={pending} onClick={invite}>
            Create invitation
          </Button>
        </div>
        <p className="page__hint">
          Invitations expire automatically. The invitee sets their own password when they accept.
        </p>
      </Panel>

      <Panel eyebrow="Team" title="Members">
        {loading && <LoadingBlock />}
        {error && <ErrorState message={error} onRetry={reload} />}
        {data && data.length === 0 && <EmptyState title="No members yet" />}
        {data && data.length > 0 && (
          <DataTable
            keyField={(row) => row.id}
            rows={data}
            columns={[
              { header: 'Name', cell: (row) => <strong>{row.full_name}</strong> },
              { header: 'Email', cell: (row) => row.email },
              { header: 'Role', cell: (row) => titleCase(row.role) },
              {
                header: 'Status',
                cell: (row) => <StatusBadge value={row.is_active ? 'active' : 'archived'} />,
              },
            ]}
          />
        )}
      </Panel>
    </div>
  );
}
