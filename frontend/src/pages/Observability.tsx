import { Panel } from '../components/ui';

export function Observability() {
  return (
    <div className="page">
      <Panel eyebrow="Telemetry" title="Signals emitted by the platform">
        <div className="policy-grid">
          <article>
            <h4>Correlation IDs</h4>
            <p>
              Every request carries or is assigned an <code>X-Correlation-ID</code> that flows
              through the API, workers and provider calls, and is bound to every structured log line.
            </p>
          </article>
          <article>
            <h4>Structured JSON logs</h4>
            <p>All application logs are single-line JSON with level, timestamp and context fields.</p>
          </article>
          <article>
            <h4>OpenTelemetry traces</h4>
            <p>
              FastAPI and SQLAlchemy are instrumented. Set <code>OTEL_ENABLED=true</code> and{' '}
              <code>OTEL_EXPORTER_ENDPOINT</code> to export OTLP spans to a collector.
            </p>
          </article>
          <article>
            <h4>Prometheus metrics</h4>
            <p>
              Exposed at <code>/metrics</code> for request, latency and process metrics.
            </p>
          </article>
          <article>
            <h4>Health & readiness</h4>
            <p>
              <code>/health/live</code> for liveness and <code>/health/ready</code> (checks Redis)
              for readiness.
            </p>
          </article>
          <article>
            <h4>Run lifecycle stream</h4>
            <p>
              <code>WS /ws/runs/&#123;run_id&#125;</code> streams run and task events; the full
              history is also persisted and available at <code>GET /api/v1/runs/&#123;id&#125;/events</code>.
            </p>
          </article>
        </div>
      </Panel>
    </div>
  );
}
