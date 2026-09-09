import { DataTable, EmptyState, ErrorState, LoadingBlock, Panel } from '../components/ui';
import { useQuery } from '../lib/useApi';
import type { AuditEvent } from '../lib/types';
import { formatDateTime, shortId, titleCase } from '../lib/format';

export function AuditLog() {
  const { data, error, loading, reload } = useQuery<AuditEvent[]>('/api/v1/audit');

  return (
    <div className="page">
      <Panel eyebrow="Audit trail" title="Security-relevant events">
        <p className="page__hint">
          Every privileged action is recorded with an actor, resource and timestamp. Audit records
          are append-only.
        </p>
        {loading && <LoadingBlock />}
        {error && <ErrorState message={error} onRetry={reload} />}
        {data && data.length === 0 && (
          <EmptyState title="No audit events yet" description="Activity will appear here as your team uses the platform." />
        )}
        {data && data.length > 0 && (
          <DataTable
            keyField={(row) => row.id}
            rows={data}
            columns={[
              { header: 'Action', cell: (row) => <strong>{titleCase(row.action)}</strong> },
              { header: 'Resource', cell: (row) => titleCase(row.resource_type) },
              { header: 'Actor', cell: (row) => (row.actor_user_id ? shortId(row.actor_user_id) : 'system') },
              { header: 'When', cell: (row) => formatDateTime(row.created_at) },
            ]}
          />
        )}
      </Panel>
    </div>
  );
}
