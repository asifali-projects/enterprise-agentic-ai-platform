import { Panel } from '../components/ui';

const POLICIES = [
  {
    title: 'Default-deny tool authorization',
    body: 'An agent can only invoke a tool after an explicit permission grant. The tool gateway rejects unauthorized calls before execution and records the denied attempt.',
  },
  {
    title: 'Human approval for high-impact actions',
    body: 'High-risk tool nodes pause the run and emit an approval-required event. Execution resumes only after an authorized reviewer approves; rejection fails the run.',
  },
  {
    title: 'Tenant and project isolation',
    body: 'Every query is scoped to the authenticated organization. Cross-tenant reads of projects, runs, memory vectors and tool permissions are not possible.',
  },
  {
    title: 'Bounded execution',
    body: 'Runs and tasks have a state machine, timeout, cancellation path and bounded retry policy. Concurrency is capped by MAX_CONCURRENCY; workers never spawn unbounded tasks.',
  },
  {
    title: 'Model output is never an authority',
    body: 'LLM responses are validated against a schema before persistence or action. Model output alone can never authorize a privileged operation.',
  },
  {
    title: 'Secrets stay out of the browser',
    body: 'Provider credentials, database URLs and keys are injected at runtime from the environment or a secret manager. Nothing sensitive is bundled into the frontend.',
  },
];

export function Governance() {
  return (
    <div className="page">
      <Panel eyebrow="Policy engine" title="Enforced platform policies">
        <div className="policy-grid">
          {POLICIES.map((policy) => (
            <article key={policy.title}>
              <h4>{policy.title}</h4>
              <p>{policy.body}</p>
            </article>
          ))}
        </div>
      </Panel>

      <Panel eyebrow="Integrations" title="Configured through environment secrets">
        <div className="policy-grid">
          <article>
            <h4>LLM gateway</h4>
            <p>
              Set <code>LLM_PROVIDER</code>, <code>LLM_BASE_URL</code>, <code>LLM_API_KEY</code> and{' '}
              <code>LLM_MODEL</code>. The default local provider is deterministic and needs no
              credentials.
            </p>
          </article>
          <article>
            <h4>PostgreSQL</h4>
            <p>Transactional state and the audit trail. Configured via <code>DATABASE_URL</code>.</p>
          </article>
          <article>
            <h4>Redis</h4>
            <p>Run queue, worker coordination and realtime event fan-out. Configured via <code>REDIS_URL</code>.</p>
          </article>
          <article>
            <h4>Qdrant</h4>
            <p>Vector store backing the memory service. Configured via <code>QDRANT_URL</code>.</p>
          </article>
        </div>
      </Panel>
    </div>
  );
}
