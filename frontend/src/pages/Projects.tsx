import { useState, type FormEvent } from 'react';
import { ApiError } from '../lib/api';
import { useAuth } from '../lib/auth';
import { useMutation, useQuery } from '../lib/useApi';
import { can } from '../lib/rbac';
import { useToast } from '../components/Toast';
import {
  Button,
  CopyId,
  DataTable,
  EmptyState,
  ErrorState,
  Field,
  LoadingBlock,
  Panel,
  StatusBadge,
} from '../components/ui';
import type { Project } from '../lib/types';

export function Projects() {
  const { user } = useAuth();
  const toast = useToast();
  const { data, error, loading, reload } = useQuery<Project[]>('/api/v1/projects');
  const { mutate, pending } = useMutation();
  const writable = can(user?.role, 'project.write');

  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [fieldError, setFieldError] = useState<string | null>(null);

  async function onCreate(event: FormEvent) {
    event.preventDefault();
    setFieldError(null);
    if (name.trim().length < 2) {
      setFieldError('Project name must be at least 2 characters.');
      return;
    }
    try {
      await mutate('/api/v1/projects', {
        method: 'POST',
        body: { name: name.trim(), description: description.trim() || null },
      });
      toast.success('Project created', `${name.trim()} is ready.`);
      setName('');
      setDescription('');
      reload();
    } catch (err) {
      toast.error('Could not create project', err instanceof ApiError ? err.message : undefined);
    }
  }

  return (
    <div className="page">
      {writable && (
        <Panel eyebrow="New project" title="Create a project">
          <form className="inline-form" onSubmit={onCreate}>
            <Field
              label="Project name"
              value={name}
              error={fieldError}
              onChange={(e) => setName(e.target.value)}
            />
            <Field
              label="Description (optional)"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
            <Button type="submit" variant="primary" loading={pending}>
              Create project
            </Button>
          </form>
        </Panel>
      )}

      <Panel eyebrow="Projects" title="All projects">
        {loading && <LoadingBlock />}
        {error && <ErrorState message={error} onRetry={reload} />}
        {data && data.length === 0 && (
          <EmptyState
            title="No projects yet"
            description={
              writable
                ? 'Create your first project using the form above.'
                : 'Ask a project administrator to create a project for you.'
            }
          />
        )}
        {data && data.length > 0 && (
          <DataTable
            keyField={(row) => row.id}
            rows={data}
            columns={[
              { header: 'Name', cell: (row) => <strong>{row.name}</strong> },
              { header: 'Description', cell: (row) => row.description || '—' },
              { header: 'Status', cell: (row) => <StatusBadge value={row.status} /> },
              { header: 'ID', cell: (row) => <CopyId value={row.id} /> },
            ]}
          />
        )}
      </Panel>
    </div>
  );
}
