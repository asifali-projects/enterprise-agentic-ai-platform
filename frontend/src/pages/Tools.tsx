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
  DataTable,
  EmptyState,
  ErrorState,
  Field,
  LoadingBlock,
  Panel,
  SelectField,
  StatusBadge,
} from '../components/ui';
import type { Tool } from '../lib/types';

export function Tools() {
  const { user } = useAuth();
  const toast = useToast();
  const writable = can(user?.role, 'tool.write');
  const { mutate, pending } = useMutation();

  const [projectId, setProjectId] = useState('');
  const tools = useQuery<Tool[]>(projectId ? `/api/v1/projects/${projectId}/tools` : null);

  const [name, setName] = useState('');
  const [risk, setRisk] = useState('low');
  const [endpoint, setEndpoint] = useState('');

  async function createTool() {
    if (name.trim().length < 2) {
      toast.error('Tool name is too short', 'Use at least 2 characters.');
      return;
    }
    try {
      await mutate(`/api/v1/projects/${projectId}/tools`, {
        method: 'POST',
        body: {
          name: name.trim(),
          description: name.trim(),
          risk_level: risk,
          input_schema: { type: 'object' },
          endpoint: endpoint.trim() || null,
        },
      });
      toast.success('Tool registered', `${name.trim()} added with ${risk} risk.`);
      setName('');
      setEndpoint('');
      tools.reload();
    } catch (err) {
      toast.error('Could not register tool', err instanceof ApiError ? err.message : undefined);
    }
  }

  return (
    <div className="page">
      <Panel eyebrow="Tool registry" title="Register a tool">
        <div className="inline-form">
          <ProjectPicker value={projectId} onChange={setProjectId} />
          {writable && projectId && (
            <>
              <Field label="Tool name" value={name} onChange={(e) => setName(e.target.value)} />
              <SelectField label="Risk level" value={risk} onChange={(e) => setRisk(e.target.value)}>
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High — requires approval</option>
              </SelectField>
              <Field
                label="HTTPS endpoint (optional)"
                value={endpoint}
                placeholder="https://tools.internal/lookup"
                onChange={(e) => setEndpoint(e.target.value)}
              />
              <Button variant="primary" loading={pending} onClick={createTool}>
                Register tool
              </Button>
            </>
          )}
        </div>
        <p className="page__hint">
          Tools are default-deny. An agent can only call a tool after an explicit permission grant,
          and high-risk tools always pause for human approval inside a workflow run.
        </p>
      </Panel>

      {!projectId && <EmptyState title="Select a project" description="Tools belong to a project." />}

      {projectId && (
        <Panel eyebrow="Tools" title="Registered tools">
          {tools.loading && <LoadingBlock />}
          {tools.error && <ErrorState message={tools.error} onRetry={tools.reload} />}
          {tools.data && tools.data.length === 0 && (
            <EmptyState title="No tools in this project" />
          )}
          {tools.data && tools.data.length > 0 && (
            <DataTable
              keyField={(row) => row.id}
              rows={tools.data}
              columns={[
                { header: 'Name', cell: (row) => <strong>{row.name}</strong> },
                { header: 'Risk', cell: (row) => <StatusBadge value={row.risk_level} /> },
                { header: 'Enabled', cell: (row) => (row.enabled ? 'Yes' : 'No') },
                { header: 'Endpoint', cell: (row) => row.endpoint || 'Authorization-only' },
                { header: 'ID', cell: (row) => <CopyId value={row.id} /> },
              ]}
            />
          )}
        </Panel>
      )}
    </div>
  );
}
