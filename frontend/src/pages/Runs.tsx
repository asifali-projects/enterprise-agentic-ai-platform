import { useEffect, useRef, useState } from 'react';
import { ApiError } from '../lib/api';
import { useAuth } from '../lib/auth';
import { can } from '../lib/rbac';
import { useMutation, useQuery } from '../lib/useApi';
import { useToast } from '../components/Toast';
import { ProjectPicker } from '../components/ProjectPicker';
import {
  Button,
  DataTable,
  Drawer,
  EmptyState,
  ErrorState,
  LoadingBlock,
  Panel,
  SelectField,
  StatusBadge,
} from '../components/ui';
import type { Run, RunEvent, RunTask, Workflow } from '../lib/types';
import { formatRelative, shortId } from '../lib/format';
import { runEventsSocketUrl } from '../lib/ws';

export function Runs() {
  const { user } = useAuth();
  const toast = useToast();
  const canLaunch = can(user?.role, 'run.launch');
  const canCancel = can(user?.role, 'run.cancel');
  const { mutate, pending } = useMutation();

  const runs = useQuery<Run[]>('/api/v1/runs');
  const [projectId, setProjectId] = useState('');
  const [workflowId, setWorkflowId] = useState('');
  const workflows = useQuery<Workflow[]>(
    projectId ? `/api/v1/projects/${projectId}/workflows` : null,
  );
  const [selected, setSelected] = useState<Run | null>(null);

  async function launch() {
    if (!projectId || !workflowId) {
      toast.error('Choose a project and workflow', 'Both are required to launch a run.');
      return;
    }
    try {
      const run = await mutate<Run>('/api/v1/runs', {
        method: 'POST',
        body: {
          project_id: projectId,
          workflow_id: workflowId,
          input: { source: 'console' },
          idempotency_key: crypto.randomUUID(),
        },
      });
      toast.success('Run queued', `Run ${shortId(run.id)} is now executing.`);
      runs.reload();
    } catch (err) {
      toast.error('Could not launch run', err instanceof ApiError ? err.message : undefined);
    }
  }

  async function cancel(run: Run) {
    try {
      await mutate(`/api/v1/runs/${run.id}/cancel`, { method: 'POST' });
      toast.success('Run cancelled', `Run ${shortId(run.id)} was cancelled.`);
      runs.reload();
    } catch (err) {
      toast.error('Could not cancel run', err instanceof ApiError ? err.message : undefined);
    }
  }

  return (
    <div className="page">
      {canLaunch && (
        <Panel eyebrow="Launch" title="Run a published workflow">
          <div className="inline-form">
            <ProjectPicker
              value={projectId}
              onChange={(id) => {
                setProjectId(id);
                setWorkflowId('');
              }}
            />
            <SelectField
              label="Workflow"
              value={workflowId}
              onChange={(e) => setWorkflowId(e.target.value)}
            >
              <option value="">Select a workflow…</option>
              {(workflows.data ?? []).map((workflow) => (
                <option key={workflow.id} value={workflow.id}>
                  {workflow.name}
                </option>
              ))}
            </SelectField>
            <Button variant="primary" loading={pending} onClick={launch}>
              Launch run
            </Button>
          </div>
        </Panel>
      )}

      <Panel
        eyebrow="Runs"
        title="Recent runs"
        actions={<Button onClick={runs.reload}>Refresh</Button>}
      >
        {runs.loading && <LoadingBlock />}
        {runs.error && <ErrorState message={runs.error} onRetry={runs.reload} />}
        {runs.data && runs.data.length === 0 && (
          <EmptyState
            title="No runs yet"
            description="Launch a published workflow to see run history and live progress here."
          />
        )}
        {runs.data && runs.data.length > 0 && (
          <DataTable
            keyField={(row) => row.id}
            rows={runs.data}
            columns={[
              { header: 'Status', cell: (row) => <StatusBadge value={row.status} /> },
              { header: 'Run', cell: (row) => <code>{shortId(row.id)}</code> },
              { header: 'Created', cell: (row) => formatRelative(row.created_at) },
              {
                header: '',
                cell: (row) => (
                  <div className="record-list__actions">
                    <Button onClick={() => setSelected(row)}>Inspect</Button>
                    {canCancel &&
                      !['succeeded', 'failed', 'cancelled', 'timed_out'].includes(row.status) && (
                        <Button variant="danger" onClick={() => cancel(row)}>
                          Cancel
                        </Button>
                      )}
                  </div>
                ),
              },
            ]}
          />
        )}
      </Panel>

      {selected && <RunDrawer run={selected} onClose={() => setSelected(null)} />}
    </div>
  );
}

function RunDrawer({ run, onClose }: { run: Run; onClose: () => void }) {
  const tasks = useQuery<RunTask[]>(`/api/v1/runs/${run.id}/tasks`);
  const history = useQuery<RunEvent[]>(`/api/v1/runs/${run.id}/events`);
  const [live, setLive] = useState<string[]>([]);
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const socket = new WebSocket(runEventsSocketUrl(run.id));
    socketRef.current = socket;
    socket.onmessage = (message) => {
      try {
        const parsed = JSON.parse(message.data);
        if (parsed.event && parsed.event !== 'HEARTBEAT') {
          setLive((current) => [...current, parsed.event]);
        }
      } catch {
        /* ignore malformed frames */
      }
    };
    return () => socket.close();
  }, [run.id]);

  return (
    <Drawer title={`Run ${shortId(run.id)}`} onClose={onClose}>
      <div className="run-detail">
        <p>
          <StatusBadge value={run.status} />
        </p>
        {run.error && <p className="form-error">{run.error}</p>}

        <h4>Tasks</h4>
        {tasks.loading && <LoadingBlock />}
        {tasks.data && tasks.data.length === 0 && <p className="page__hint">No tasks recorded.</p>}
        {tasks.data && tasks.data.length > 0 && (
          <ul className="event-list">
            {tasks.data.map((task) => (
              <li key={task.id}>
                <StatusBadge value={task.status} /> {task.task_id}
                {task.attempt > 1 && <span className="page__hint"> · attempt {task.attempt}</span>}
                {task.error && <span className="form-error"> · {task.error}</span>}
              </li>
            ))}
          </ul>
        )}

        <h4>Event history</h4>
        {history.data && (
          <ul className="event-list">
            {history.data.map((event, index) => (
              <li key={index}>
                <code>{event.event}</code>
                <span className="page__hint"> · {formatRelative(event.created_at)}</span>
              </li>
            ))}
            {live.map((event, index) => (
              <li key={`live-${index}`}>
                <code>{event}</code> <span className="badge badge--info">live</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </Drawer>
  );
}
