import { useState } from 'react';
import { ApiError } from '../lib/api';
import { useAuth } from '../lib/auth';
import { can } from '../lib/rbac';
import { useMutation, useQuery } from '../lib/useApi';
import { useToast } from '../components/Toast';
import { ProjectPicker } from '../components/ProjectPicker';
import {
  Button,
  CopyId,
  Drawer,
  EmptyState,
  ErrorState,
  Field,
  LoadingBlock,
  Panel,
  StatusBadge,
  TextAreaField,
} from '../components/ui';
import type { Workflow } from '../lib/types';

const TEMPLATE = JSON.stringify(
  {
    nodes: [
      { id: 'triage', type: 'agent' },
      { id: 'resolve', type: 'agent', depends_on: ['triage'] },
    ],
    max_concurrency: 2,
  },
  null,
  2,
);

export function Workflows() {
  const { user } = useAuth();
  const toast = useToast();
  const writable = can(user?.role, 'workflow.write');
  const { mutate, pending } = useMutation();

  const [projectId, setProjectId] = useState('');
  const workflows = useQuery<Workflow[]>(
    projectId ? `/api/v1/projects/${projectId}/workflows` : null,
  );

  const [name, setName] = useState('');
  const [editing, setEditing] = useState<Workflow | null>(null);
  const [definition, setDefinition] = useState(TEMPLATE);
  const [jsonError, setJsonError] = useState<string | null>(null);

  async function createWorkflow() {
    if (name.trim().length < 2) {
      toast.error('Workflow name is too short', 'Use at least 2 characters.');
      return;
    }
    try {
      await mutate(`/api/v1/projects/${projectId}/workflows`, {
        method: 'POST',
        body: { name: name.trim() },
      });
      toast.success('Workflow created', `${name.trim()} added.`);
      setName('');
      workflows.reload();
    } catch (err) {
      toast.error('Could not create workflow', err instanceof ApiError ? err.message : undefined);
    }
  }

  async function saveVersion() {
    if (!editing) return;
    setJsonError(null);
    let parsed: unknown;
    try {
      parsed = JSON.parse(definition);
    } catch {
      setJsonError('The definition is not valid JSON.');
      return;
    }
    try {
      await mutate(`/api/v1/projects/${projectId}/workflows/${editing.id}/versions`, {
        method: 'POST',
        body: { definition: parsed },
      });
      toast.success('Workflow version created', 'Graph validated: unique ids, no cycles.');
      setEditing(null);
      workflows.reload();
    } catch (err) {
      const message = err instanceof ApiError ? err.message : 'The workflow definition was rejected.';
      setJsonError(message);
    }
  }

  async function publish(workflow: Workflow) {
    try {
      await mutate(`/api/v1/projects/${projectId}/workflows/${workflow.id}/versions/1/publish`, {
        method: 'POST',
      });
      toast.success('Version 1 published', `${workflow.name} can now be run.`);
      workflows.reload();
    } catch (err) {
      toast.error('Publish failed', err instanceof ApiError ? err.message : undefined);
    }
  }

  return (
    <div className="page">
      <Panel eyebrow="Workflow builder" title="Compose a workflow">
        <div className="inline-form">
          <ProjectPicker value={projectId} onChange={setProjectId} />
          {writable && projectId && (
            <>
              <Field label="Workflow name" value={name} onChange={(e) => setName(e.target.value)} />
              <Button variant="primary" loading={pending} onClick={createWorkflow}>
                Create workflow
              </Button>
            </>
          )}
        </div>
        <p className="page__hint">
          A workflow version is a directed acyclic graph of nodes. Dependencies run in order;
          independent nodes run in parallel up to <code>max_concurrency</code>.
        </p>
      </Panel>

      {!projectId && (
        <EmptyState title="Select a project" description="Workflows belong to a project." />
      )}

      {projectId && (
        <Panel eyebrow="Workflows" title="Workflow registry">
          {workflows.loading && <LoadingBlock />}
          {workflows.error && <ErrorState message={workflows.error} onRetry={workflows.reload} />}
          {workflows.data && workflows.data.length === 0 && (
            <EmptyState title="No workflows in this project" />
          )}
          {workflows.data && workflows.data.length > 0 && (
            <ul className="record-list">
              {workflows.data.map((workflow) => (
                <li key={workflow.id}>
                  <div>
                    <strong>{workflow.name}</strong>
                    <span className="record-list__meta">
                      <StatusBadge value={workflow.status} /> <CopyId value={workflow.id} />
                    </span>
                  </div>
                  {writable && (
                    <div className="record-list__actions">
                      <Button onClick={() => setEditing(workflow)}>Edit definition</Button>
                      <Button onClick={() => publish(workflow)}>Publish v1</Button>
                    </div>
                  )}
                </li>
              ))}
            </ul>
          )}
        </Panel>
      )}

      {editing && (
        <Drawer title={`Definition — ${editing.name}`} onClose={() => setEditing(null)}>
          <TextAreaField
            label="Workflow definition (JSON)"
            rows={16}
            spellCheck={false}
            value={definition}
            error={jsonError}
            onChange={(e) => setDefinition(e.target.value)}
          />
          <div className="drawer__footer">
            <Button variant="ghost" onClick={() => setEditing(null)}>
              Cancel
            </Button>
            <Button variant="primary" loading={pending} onClick={saveVersion}>
              Save version
            </Button>
          </div>
        </Drawer>
      )}
    </div>
  );
}
