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
import type { Agent } from '../lib/types';

export function Agents() {
  const { user } = useAuth();
  const toast = useToast();
  const writable = can(user?.role, 'agent.write');
  const { mutate, pending } = useMutation();

  const [projectId, setProjectId] = useState('');
  const agents = useQuery<Agent[]>(projectId ? `/api/v1/projects/${projectId}/agents` : null);

  const [name, setName] = useState('');
  const [versionFor, setVersionFor] = useState<Agent | null>(null);
  const [prompt, setPrompt] = useState('You are a governed enterprise assistant. Be accurate and concise.');
  const [model, setModel] = useState('deterministic');

  async function createAgent() {
    if (name.trim().length < 2) {
      toast.error('Agent name is too short', 'Use at least 2 characters.');
      return;
    }
    try {
      await mutate(`/api/v1/projects/${projectId}/agents`, {
        method: 'POST',
        body: { name: name.trim() },
      });
      toast.success('Agent created', `${name.trim()} added to the registry.`);
      setName('');
      agents.reload();
    } catch (err) {
      toast.error('Could not create agent', err instanceof ApiError ? err.message : undefined);
    }
  }

  async function createVersion() {
    if (!versionFor) return;
    try {
      await mutate(`/api/v1/projects/${projectId}/agents/${versionFor.id}/versions`, {
        method: 'POST',
        body: { system_prompt: prompt, model_provider: 'local', model_name: model, config: {} },
      });
      toast.success('Version created', `A new version of ${versionFor.name} is ready to publish.`);
      setVersionFor(null);
      agents.reload();
    } catch (err) {
      toast.error('Could not create version', err instanceof ApiError ? err.message : undefined);
    }
  }

  async function publish(agent: Agent) {
    try {
      await mutate(`/api/v1/projects/${projectId}/agents/${agent.id}/versions/1/publish`, {
        method: 'POST',
      });
      toast.success('Version 1 published', `${agent.name} is now active.`);
      agents.reload();
    } catch (err) {
      toast.error('Publish failed', err instanceof ApiError ? err.message : undefined);
    }
  }

  return (
    <div className="page">
      <Panel eyebrow="Agent registry" title="Manage agents">
        <div className="inline-form">
          <ProjectPicker value={projectId} onChange={setProjectId} />
          {writable && projectId && (
            <>
              <Field label="New agent name" value={name} onChange={(e) => setName(e.target.value)} />
              <Button variant="primary" loading={pending} onClick={createAgent}>
                Create agent
              </Button>
            </>
          )}
        </div>
      </Panel>

      {!projectId && (
        <EmptyState title="Select a project" description="Agents belong to a project." />
      )}

      {projectId && (
        <Panel eyebrow="Agents" title="Registered agents">
          {agents.loading && <LoadingBlock />}
          {agents.error && <ErrorState message={agents.error} onRetry={agents.reload} />}
          {agents.data && agents.data.length === 0 && (
            <EmptyState
              title="No agents in this project"
              description={writable ? 'Create one with the form above.' : 'No agents have been registered yet.'}
            />
          )}
          {agents.data && agents.data.length > 0 && (
            <ul className="record-list">
              {agents.data.map((agent) => (
                <li key={agent.id}>
                  <div>
                    <strong>{agent.name}</strong>
                    <span className="record-list__meta">
                      <StatusBadge value={agent.status} /> <CopyId value={agent.id} />
                    </span>
                  </div>
                  {writable && (
                    <div className="record-list__actions">
                      <Button onClick={() => setVersionFor(agent)}>New version</Button>
                      <Button onClick={() => publish(agent)}>Publish v1</Button>
                    </div>
                  )}
                </li>
              ))}
            </ul>
          )}
        </Panel>
      )}

      {versionFor && (
        <Drawer title={`New version — ${versionFor.name}`} onClose={() => setVersionFor(null)}>
          <TextAreaField
            label="System prompt"
            rows={8}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
          />
          <Field label="Model name" value={model} onChange={(e) => setModel(e.target.value)} />
          <div className="drawer__footer">
            <Button variant="ghost" onClick={() => setVersionFor(null)}>
              Cancel
            </Button>
            <Button variant="primary" loading={pending} onClick={createVersion}>
              Create version
            </Button>
          </div>
        </Drawer>
      )}
    </div>
  );
}
