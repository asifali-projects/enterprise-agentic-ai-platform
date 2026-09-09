import { ApiError } from '../lib/api';
import { useAuth } from '../lib/auth';
import { can } from '../lib/rbac';
import { useMutation, useQuery } from '../lib/useApi';
import { useToast } from '../components/Toast';
import { Button, DataTable, EmptyState, ErrorState, LoadingBlock, Panel, StatusBadge } from '../components/ui';
import type { Approval } from '../lib/types';
import { formatRelative, shortId } from '../lib/format';

export function Approvals() {
  const { user } = useAuth();
  const toast = useToast();
  const decider = can(user?.role, 'approval.decide');
  const { data, error, loading, reload } = useQuery<Approval[]>('/api/v1/approvals');
  const { mutate, pending } = useMutation();

  async function decide(approval: Approval, decision: 'approved' | 'rejected') {
    try {
      await mutate(`/api/v1/approvals/${approval.id}/decision`, {
        method: 'POST',
        body: { decision },
      });
      toast.success(
        decision === 'approved' ? 'Approval granted' : 'Approval rejected',
        decision === 'approved'
          ? 'The run has been resumed.'
          : 'The run has been marked as failed.',
      );
      reload();
    } catch (err) {
      toast.error('Could not record decision', err instanceof ApiError ? err.message : undefined);
    }
  }

  const pendingApprovals = (data ?? []).filter((approval) => approval.status === 'pending');

  return (
    <div className="page">
      <Panel eyebrow="Human approval" title="Approval queue">
        <p className="page__hint">
          High-impact tool actions pause the workflow and wait here. Only an authorized reviewer can
          release them. Model output alone never authorizes a privileged action.
        </p>
        {loading && <LoadingBlock />}
        {error && <ErrorState message={error} onRetry={reload} />}
        {data && pendingApprovals.length === 0 && (
          <EmptyState title="Nothing waiting" description="There are no pending approvals right now." />
        )}
        {pendingApprovals.length > 0 && (
          <DataTable
            keyField={(row) => row.id}
            rows={pendingApprovals}
            columns={[
              { header: 'Reason', cell: (row) => row.reason },
              { header: 'Run', cell: (row) => <code>{shortId(row.run_id)}</code> },
              { header: 'Status', cell: (row) => <StatusBadge value={row.status} /> },
              {
                header: '',
                cell: (row) =>
                  decider ? (
                    <div className="record-list__actions">
                      <Button
                        variant="primary"
                        loading={pending}
                        onClick={() => decide(row, 'approved')}
                      >
                        Approve
                      </Button>
                      <Button variant="danger" loading={pending} onClick={() => decide(row, 'rejected')}>
                        Reject
                      </Button>
                    </div>
                  ) : (
                    <span className="page__hint">Requires an approver role</span>
                  ),
              },
            ]}
          />
        )}
      </Panel>

      {data && data.length > pendingApprovals.length && (
        <Panel eyebrow="History" title="Decided approvals">
          <DataTable
            keyField={(row) => row.id}
            rows={data.filter((approval) => approval.status !== 'pending')}
            columns={[
              { header: 'Reason', cell: (row) => row.reason },
              { header: 'Decision', cell: (row) => <StatusBadge value={row.status} /> },
              { header: 'Decided', cell: (row) => formatRelative(row.decided_at) },
            ]}
          />
        </Panel>
      )}
    </div>
  );
}
