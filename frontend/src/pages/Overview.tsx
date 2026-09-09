import { Link } from 'react-router-dom';
import { EmptyState, ErrorState, LoadingBlock, Panel } from '../components/ui';
import { useAuth } from '../lib/auth';
import { useQuery } from '../lib/useApi';
import type { DashboardCounts } from '../lib/types';

const STAGES = ['Agent', 'Tool', 'Policy', 'Workflow', 'Run', 'Approval', 'Evaluation', 'Audit'];

export function Overview() {
  const { user } = useAuth();
  const { data, error, loading, reload } = useQuery<{ counts: DashboardCounts }>('/api/v1/dashboard');

  const metrics: [string, number, string][] = data
    ? [
        ['Projects', data.counts.projects, '/projects'],
        ['Agents', data.counts.agents, '/agents'],
        ['Tools', data.counts.tools, '/tools'],
        ['Workflows', data.counts.workflows, '/workflows'],
        ['Runs', data.counts.runs, '/runs'],
        ['Pending approvals', data.counts.approvals, '/approvals'],
      ]
    : [];

  return (
    <div className="page">
      <p className="page__lead">
        Welcome back, {user?.full_name?.split(' ')[0] ?? 'operator'}. Here is the current state of{' '}
        {user?.organization?.name ?? 'your organization'}.
      </p>

      {loading && <LoadingBlock label="Loading organization metrics…" />}
      {error && <ErrorState message={error} onRetry={reload} />}

      {data && (
        <>
          <div className="metric-grid">
            {metrics.map(([label, value, to]) => (
              <Link key={label} to={to} className="metric-card">
                <span>{label}</span>
                <strong>{value}</strong>
              </Link>
            ))}
          </div>

          <Panel eyebrow="Operating model" title="Govern → build → execute → assure → audit">
            <ol className="flow">
              {STAGES.map((stage, index) => (
                <li key={stage}>
                  <span className="flow__step">{index + 1}</span>
                  {stage}
                </li>
              ))}
            </ol>
            <p className="page__hint">
              Every long-running operation has an explicit state machine, timeout, cancellation and
              retry policy, and produces an auditable outcome.
            </p>
          </Panel>

          {data.counts.projects === 0 && (
            <EmptyState
              title="Start with a project"
              description="Projects scope agents, tools, workflows and memory. Create one to begin."
              action={
                <Link className="btn btn--primary" to="/projects">
                  Create a project
                </Link>
              }
            />
          )}
        </>
      )}
    </div>
  );
}
