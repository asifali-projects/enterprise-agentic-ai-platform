import { useEffect } from 'react';
import { useQuery } from '../lib/useApi';
import type { Project } from '../lib/types';
import { SelectField } from './ui';

interface Props {
  value: string;
  onChange: (projectId: string) => void;
  label?: string;
}

/** Shared project selector. Auto-selects the only project when there is exactly one. */
export function ProjectPicker({ value, onChange, label = 'Project' }: Props) {
  const { data } = useQuery<Project[]>('/api/v1/projects');

  useEffect(() => {
    if (!value && data && data.length === 1) onChange(data[0].id);
  }, [data, value, onChange]);

  return (
    <SelectField label={label} value={value} onChange={(e) => onChange(e.target.value)}>
      <option value="">Select a project…</option>
      {(data ?? []).map((project) => (
        <option key={project.id} value={project.id}>
          {project.name}
        </option>
      ))}
    </SelectField>
  );
}

export function useProjects() {
  return useQuery<Project[]>('/api/v1/projects');
}
