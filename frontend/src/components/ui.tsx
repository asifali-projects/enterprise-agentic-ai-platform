import { useState } from 'react';
import type {
  ButtonHTMLAttributes,
  InputHTMLAttributes,
  ReactNode,
  SelectHTMLAttributes,
  TextareaHTMLAttributes,
} from 'react';

/* ---------------------------------------------------------------- CopyId */

/** Full identifier with a one-click copy affordance — used wherever an id must
 *  be pasted elsewhere (e.g. into a workflow definition). */
export function CopyId({ value }: { value: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      type="button"
      className="copy-id"
      title="Click to copy"
      onClick={async () => {
        try {
          await navigator.clipboard.writeText(value);
          setCopied(true);
          setTimeout(() => setCopied(false), 1200);
        } catch {
          /* clipboard unavailable */
        }
      }}
    >
      <code>{value}</code>
      <span aria-hidden>{copied ? '✓' : '⧉'}</span>
    </button>
  );
}

/* ------------------------------------------------------------------ Button */

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  loading?: boolean;
}

export function Button({
  variant = 'secondary',
  loading = false,
  disabled,
  children,
  className = '',
  ...rest
}: ButtonProps) {
  return (
    <button
      className={`btn btn--${variant} ${className}`}
      disabled={disabled || loading}
      {...rest}
    >
      {loading && <span className="btn__spinner" aria-hidden />}
      <span>{children}</span>
    </button>
  );
}

/* ------------------------------------------------------------------- Field */

interface FieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string | null;
  hint?: string;
}

export function Field({ label, error, hint, id, ...rest }: FieldProps) {
  const fieldId = id || `field-${label.replace(/\s+/g, '-').toLowerCase()}`;
  return (
    <div className={`field ${error ? 'field--invalid' : ''}`}>
      <label htmlFor={fieldId}>{label}</label>
      <input id={fieldId} aria-invalid={Boolean(error)} {...rest} />
      {error ? (
        <p className="field__error">{error}</p>
      ) : hint ? (
        <p className="field__hint">{hint}</p>
      ) : null}
    </div>
  );
}

interface SelectFieldProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label: string;
  error?: string | null;
  children: ReactNode;
}

export function SelectField({ label, error, id, children, ...rest }: SelectFieldProps) {
  const fieldId = id || `select-${label.replace(/\s+/g, '-').toLowerCase()}`;
  return (
    <div className={`field ${error ? 'field--invalid' : ''}`}>
      <label htmlFor={fieldId}>{label}</label>
      <select id={fieldId} {...rest}>
        {children}
      </select>
      {error && <p className="field__error">{error}</p>}
    </div>
  );
}

interface TextAreaFieldProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label: string;
  error?: string | null;
  hint?: string;
}

export function TextAreaField({ label, error, hint, id, ...rest }: TextAreaFieldProps) {
  const fieldId = id || `textarea-${label.replace(/\s+/g, '-').toLowerCase()}`;
  return (
    <div className={`field ${error ? 'field--invalid' : ''}`}>
      <label htmlFor={fieldId}>{label}</label>
      <textarea id={fieldId} {...rest} />
      {error ? <p className="field__error">{error}</p> : hint ? <p className="field__hint">{hint}</p> : null}
    </div>
  );
}

/* ------------------------------------------------------------- Status views */

export function LoadingBlock({ label = 'Loading…' }: { label?: string }) {
  return (
    <div className="state state--loading">
      <span className="spinner" aria-hidden />
      <p>{label}</p>
    </div>
  );
}

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="state state--empty">
      <p className="state__title">{title}</p>
      {description && <p className="state__description">{description}</p>}
      {action}
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="state state--error">
      <p className="state__title">Something went wrong</p>
      <p className="state__description">{message}</p>
      {onRetry && (
        <Button variant="secondary" onClick={onRetry}>
          Try again
        </Button>
      )}
    </div>
  );
}

/* -------------------------------------------------------------------- Cards */

export function Panel({
  title,
  eyebrow,
  actions,
  children,
}: {
  title: string;
  eyebrow?: string;
  actions?: ReactNode;
  children: ReactNode;
}) {
  return (
    <section className="panel">
      <header className="panel__header">
        <div>
          {eyebrow && <p className="eyebrow">{eyebrow}</p>}
          <h3>{title}</h3>
        </div>
        {actions && <div className="panel__actions">{actions}</div>}
      </header>
      {children}
    </section>
  );
}

const TONE_BY_STATUS: Record<string, string> = {
  succeeded: 'ok',
  active: 'ok',
  approved: 'ok',
  published: 'ok',
  running: 'info',
  queued: 'info',
  pending: 'warn',
  waiting_approval: 'warn',
  draft: 'muted',
  archived: 'muted',
  failed: 'danger',
  rejected: 'danger',
  cancelled: 'danger',
  timed_out: 'danger',
};

export function StatusBadge({ value }: { value: string }) {
  const tone = TONE_BY_STATUS[value?.toLowerCase?.()] || 'muted';
  return <span className={`badge badge--${tone}`}>{value?.replace(/_/g, ' ')}</span>;
}

/* -------------------------------------------------------------------- Table */

interface Column<T> {
  header: string;
  cell: (row: T) => ReactNode;
}

export function DataTable<T>({
  columns,
  rows,
  keyField,
}: {
  columns: Column<T>[];
  rows: T[];
  keyField: (row: T) => string;
}) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column.header}>{column.header}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={keyField(row)}>
              {columns.map((column) => (
                <td key={column.header}>{column.cell(row)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function Drawer({
  title,
  onClose,
  children,
}: {
  title: string;
  onClose: () => void;
  children: ReactNode;
}) {
  return (
    <div className="drawer-backdrop" onClick={onClose}>
      <div className="drawer" role="dialog" aria-label={title} onClick={(e) => e.stopPropagation()}>
        <header className="drawer__header">
          <h3>{title}</h3>
          <button className="drawer__close" onClick={onClose} aria-label="Close">
            ×
          </button>
        </header>
        <div className="drawer__body">{children}</div>
      </div>
    </div>
  );
}
