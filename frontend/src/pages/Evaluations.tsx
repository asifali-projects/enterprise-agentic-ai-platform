import { useState } from 'react';
import { ApiError } from '../lib/api';
import { useAuth } from '../lib/auth';
import { can } from '../lib/rbac';
import { useMutation, useQuery } from '../lib/useApi';
import { useToast } from '../components/Toast';
import { ProjectPicker } from '../components/ProjectPicker';
import {
  Button,
  DataTable,
  EmptyState,
  ErrorState,
  Field,
  LoadingBlock,
  Panel,
  StatusBadge,
} from '../components/ui';
import type { Evaluation } from '../lib/types';

export function Evaluations() {
  const { user } = useAuth();
  const toast = useToast();
  const writable = can(user?.role, 'evaluation.write');
  const { mutate, pending } = useMutation();

  const [projectId, setProjectId] = useState('');
  const evaluations = useQuery<Evaluation[]>(
    projectId ? `/api/v1/projects/${projectId}/evaluations` : null,
  );

  const [name, setName] = useState('');
  const [threshold, setThreshold] = useState('0.8');

  async function createEvaluation() {
    const parsed = Number(threshold);
    if (name.trim().length < 2) {
      toast.error('Evaluation name is too short', 'Use at least 2 characters.');
      return;
    }
    if (Number.isNaN(parsed) || parsed < 0 || parsed > 1) {
      toast.error('Threshold must be between 0 and 1');
      return;
    }
    try {
      await mutate(`/api/v1/projects/${projectId}/evaluations`, {
        method: 'POST',
        body: { name: name.trim(), dataset: { cases: [] }, threshold: parsed },
      });
      toast.success('Evaluation created', 'Add cases to the dataset, then run it.');
      setName('');
      evaluations.reload();
    } catch (err) {
      toast.error('Could not create evaluation', err instanceof ApiError ? err.message : undefined);
    }
  }

  async function runEvaluation(evaluation: Evaluation) {
    try {
      const result = await mutate<{ score: number | null; passed: boolean | null }>(
        `/api/v1/projects/${projectId}/evaluations/${evaluation.id}/run`,
        { method: 'POST' },
      );
      toast.success(
        'Evaluation complete',
        `Score ${result.score ?? 0} · ${result.passed ? 'passed' : 'below threshold'}`,
      );
      evaluations.reload();
    } catch (err) {
      toast.error('Evaluation run failed', err instanceof ApiError ? err.message : undefined);
    }
  }

  return (
    <div className="page">
      <Panel eyebrow="Evaluation service" title="Create an evaluation">
        <div className="inline-form">
          <ProjectPicker value={projectId} onChange={setProjectId} />
          {writable && projectId && (
            <>
              <Field label="Evaluation name" value={name} onChange={(e) => setName(e.target.value)} />
              <Field
                label="Pass threshold"
                type="number"
                min={0}
                max={1}
                step={0.05}
                value={threshold}
                onChange={(e) => setThreshold(e.target.value)}
              />
              <Button variant="primary" loading={pending} onClick={createEvaluation}>
                Create evaluation
              </Button>
            </>
          )}
        </div>
        <p className="page__hint">
          Evaluations score agent versions against a fixed dataset. Attach a regression gate to block
          releases when quality drops beyond the allowed margin.
        </p>
      </Panel>

      {!projectId && (
        <EmptyState title="Select a project" description="Evaluations belong to a project." />
      )}

      {projectId && (
        <Panel eyebrow="Evaluations" title="Datasets">
          {evaluations.loading && <LoadingBlock />}
          {evaluations.error && (
            <ErrorState message={evaluations.error} onRetry={evaluations.reload} />
          )}
          {evaluations.data && evaluations.data.length === 0 && (
            <EmptyState title="No evaluations yet" />
          )}
          {evaluations.data && evaluations.data.length > 0 && (
            <DataTable
              keyField={(row) => row.id}
              rows={evaluations.data}
              columns={[
                { header: 'Name', cell: (row) => <strong>{row.name}</strong> },
                { header: 'Threshold', cell: (row) => row.threshold },
                {
                  header: 'Last score',
                  cell: (row) =>
                    row.last_score == null ? (
                      <span className="page__hint">Not run</span>
                    ) : (
                      <StatusBadge
                        value={row.last_score >= row.threshold ? 'succeeded' : 'failed'}
                      />
                    ),
                },
                {
                  header: '',
                  cell: (row) =>
                    writable ? (
                      <Button loading={pending} onClick={() => runEvaluation(row)}>
                        Run now
                      </Button>
                    ) : null,
                },
              ]}
            />
          )}
        </Panel>
      )}
    </div>
  );
}
