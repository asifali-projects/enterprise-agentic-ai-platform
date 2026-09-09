import { useMemo, useState, type FormEvent } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { ApiError } from '../lib/api';
import { useAuth } from '../lib/auth';
import { useToast } from '../components/Toast';
import { Button, Field } from '../components/ui';
import { email as emailRule, passwordRules, runValidators, required } from '../lib/validation';

type Mode = 'signin' | 'signup' | 'demo';

const MODE_COPY: Record<Mode, { tab: string; cta: string; heading: string }> = {
  signin: { tab: 'Sign in', cta: 'Sign in', heading: 'Sign in to your control plane' },
  signup: { tab: 'Create account', cta: 'Create organization', heading: 'Create your organization' },
  demo: { tab: 'Guided demo', cta: 'Open demo workspace', heading: 'Explore a demo tenant' },
};

interface FormShape {
  full_name: string;
  email: string;
  password: string;
  organization_name: string;
}

const EMPTY: FormShape = { full_name: '', email: '', password: '', organization_name: '' };

export function AuthPage() {
  const { login, register, startDemo } = useAuth();
  const toast = useToast();
  const navigate = useNavigate();
  const location = useLocation();
  const redirectTo = (location.state as { from?: string } | null)?.from ?? '/overview';

  const [mode, setMode] = useState<Mode>('signin');
  const [form, setForm] = useState<FormShape>(EMPTY);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const passwordChecklist = useMemo(
    () => passwordRules.map((rule) => ({ label: rule.label, met: rule.test(form.password) })),
    [form.password],
  );

  function update(field: keyof FormShape, value: string) {
    setForm((current) => ({ ...current, [field]: value }));
    setErrors((current) => {
      if (!current[field]) return current;
      const next = { ...current };
      delete next[field];
      return next;
    });
  }

  function validate(): boolean {
    const rules: Record<string, Parameters<typeof runValidators>[0][string]> = {};
    if (mode !== 'signin') rules.full_name = [required('Full name')];
    if (mode !== 'demo') {
      rules.email = [emailRule];
      rules.password =
        mode === 'signup'
          ? [
              (value) =>
                passwordRules.every((rule) => rule.test(value))
                  ? null
                  : 'Choose a password that meets every requirement below.',
            ]
          : [required('Password')];
    }
    if (mode === 'signup') rules.organization_name = [required('Company name')];
    const found = runValidators(rules, form as unknown as Record<string, string>);
    setErrors(found);
    return Object.keys(found).length === 0;
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setFormError(null);
    if (!validate()) return;
    setSubmitting(true);
    try {
      if (mode === 'signin') {
        await login({ email: form.email.trim(), password: form.password });
        toast.success('Signed in', 'Welcome back.');
      } else if (mode === 'signup') {
        await register({
          full_name: form.full_name.trim(),
          email: form.email.trim(),
          password: form.password,
          organization_name: form.organization_name.trim(),
        });
        toast.success('Organization created', `You are the owner of ${form.organization_name.trim()}.`);
      } else {
        await startDemo({ full_name: form.full_name.trim() || undefined });
        toast.success('Demo workspace ready', 'Sample projects, agents and workflows are loaded.');
      }
      navigate(redirectTo, { replace: true });
    } catch (error) {
      if (error instanceof ApiError) {
        setErrors((current) => ({ ...current, ...error.fieldErrors }));
        setFormError(error.message);
      } else {
        setFormError('Something went wrong. Please try again.');
      }
    } finally {
      setSubmitting(false);
    }
  }

  function switchMode(next: Mode) {
    setMode(next);
    setErrors({});
    setFormError(null);
  }

  return (
    <div className="auth">
      <div className="auth__intro">
        <p className="eyebrow">Enterprise Agentic AI Operating Platform</p>
        <h1>Govern, run and audit AI agents in production.</h1>
        <p className="auth__lead">
          One tenant-isolated control plane for agent registries, tool permissions, workflow
          orchestration, human approvals, evaluations and a complete audit trail.
        </p>
        <ul className="auth__points">
          <li>Default-deny tool authorization with human approval gates</li>
          <li>Bounded parallel execution with timeouts, cancellation and retries</li>
          <li>Reproducible evaluations and regression gates for every agent version</li>
        </ul>
      </div>

      <div className="auth__card">
        <div className="auth__tabs" role="tablist">
          {(Object.keys(MODE_COPY) as Mode[]).map((value) => (
            <button
              key={value}
              role="tab"
              aria-selected={mode === value}
              className={mode === value ? 'is-active' : ''}
              onClick={() => switchMode(value)}
            >
              {MODE_COPY[value].tab}
            </button>
          ))}
        </div>

        <h2>{MODE_COPY[mode].heading}</h2>

        <form onSubmit={onSubmit} noValidate>
          {mode !== 'signin' && (
            <Field
              label="Full name"
              autoComplete="name"
              value={form.full_name}
              error={errors.full_name}
              onChange={(e) => update('full_name', e.target.value)}
            />
          )}

          {mode !== 'demo' && (
            <>
              <Field
                label="Work email"
                type="email"
                autoComplete="email"
                value={form.email}
                error={errors.email}
                onChange={(e) => update('email', e.target.value)}
              />
              <Field
                label="Password"
                type="password"
                autoComplete={mode === 'signup' ? 'new-password' : 'current-password'}
                value={form.password}
                error={errors.password}
                onChange={(e) => update('password', e.target.value)}
              />
            </>
          )}

          {mode === 'signup' && (
            <>
              <ul className="password-checklist">
                {passwordChecklist.map((item) => (
                  <li key={item.label} className={item.met ? 'is-met' : ''}>
                    <span aria-hidden>{item.met ? '✓' : '○'}</span> {item.label}
                  </li>
                ))}
              </ul>
              <Field
                label="Company name"
                autoComplete="organization"
                value={form.organization_name}
                error={errors.organization_name}
                onChange={(e) => update('organization_name', e.target.value)}
              />
            </>
          )}

          {mode === 'demo' && (
            <p className="auth__demo-note">
              The demo tenant is fully isolated and expires automatically. No email or password is
              required.
            </p>
          )}

          {formError && <p className="form-error" role="alert">{formError}</p>}

          <Button type="submit" variant="primary" loading={submitting}>
            {MODE_COPY[mode].cta}
          </Button>
        </form>

        <p className="auth__switch">
          {mode === 'signin' ? (
            <>
              New here?{' '}
              <button onClick={() => switchMode('signup')}>Create an organization</button>
            </>
          ) : (
            <>
              Already have an account?{' '}
              <button onClick={() => switchMode('signin')}>Sign in</button>
            </>
          )}
        </p>
        <p className="auth__fineprint">
          No secrets are stored in the browser. Every privileged operation is authorized by the API.
        </p>
      </div>
    </div>
  );
}
