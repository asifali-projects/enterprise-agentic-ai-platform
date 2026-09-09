import { useState } from 'react';
import { ApiError } from '../lib/api';
import { useAuth } from '../lib/auth';
import { can } from '../lib/rbac';
import { useMutation } from '../lib/useApi';
import { useToast } from '../components/Toast';
import { ProjectPicker } from '../components/ProjectPicker';
import { Button, DataTable, EmptyState, Field, Panel, TextAreaField } from '../components/ui';

interface MemoryHit {
  id: string;
  score: number;
  key: string;
  text: string;
}

export function Memory() {
  const { user } = useAuth();
  const toast = useToast();
  const writable = can(user?.role, 'memory.write');
  const { mutate, pending } = useMutation();

  const [projectId, setProjectId] = useState('');
  const [key, setKey] = useState('');
  const [text, setText] = useState('');
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<MemoryHit[] | null>(null);

  async function store() {
    if (!projectId) return toast.error('Select a project first');
    if (!key.trim() || !text.trim()) return toast.error('A key and text are both required');
    try {
      await mutate(`/api/v1/projects/${projectId}/memory`, {
        method: 'POST',
        body: { key: key.trim(), text: text.trim(), metadata: { source: 'console' } },
      });
      toast.success('Memory stored', `Item "${key.trim()}" is now searchable.`);
      setKey('');
      setText('');
    } catch (err) {
      toast.error('Could not store memory', err instanceof ApiError ? err.message : undefined);
    }
  }

  async function search() {
    if (!projectId) return toast.error('Select a project first');
    if (!query.trim()) return toast.error('Enter a search query');
    try {
      const hits = await mutate<MemoryHit[]>(`/api/v1/projects/${projectId}/memory/search`, {
        method: 'POST',
        body: { query: query.trim(), limit: 10 },
      });
      setResults(hits);
    } catch (err) {
      toast.error('Search failed', err instanceof ApiError ? err.message : undefined);
    }
  }

  return (
    <div className="page">
      <Panel eyebrow="Memory service" title="Project memory">
        <ProjectPicker value={projectId} onChange={setProjectId} />
        {!projectId && (
          <EmptyState title="Select a project" description="Memory is scoped per project and tenant." />
        )}
        {projectId && (
          <div className="split">
            {writable && (
              <div>
                <h4>Store an item</h4>
                <Field label="Key" value={key} onChange={(e) => setKey(e.target.value)} />
                <TextAreaField
                  label="Text"
                  rows={5}
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                />
                <Button variant="primary" loading={pending} onClick={store}>
                  Store memory
                </Button>
              </div>
            )}
            <div>
              <h4>Semantic search</h4>
              <Field label="Query" value={query} onChange={(e) => setQuery(e.target.value)} />
              <Button loading={pending} onClick={search}>
                Search
              </Button>
              {results && results.length === 0 && (
                <p className="page__hint">No matching memory items.</p>
              )}
              {results && results.length > 0 && (
                <DataTable
                  keyField={(row) => row.id}
                  rows={results}
                  columns={[
                    { header: 'Score', cell: (row) => row.score.toFixed(3) },
                    { header: 'Key', cell: (row) => row.key },
                    { header: 'Text', cell: (row) => row.text },
                  ]}
                />
              )}
            </div>
          </div>
        )}
      </Panel>
    </div>
  );
}
