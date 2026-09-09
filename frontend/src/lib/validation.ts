/** Client-side form validation with professional, specific messages. */

export type Validator = (value: string, form?: Record<string, string>) => string | null;

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export const required =
  (label: string): Validator =>
  (value) =>
    value.trim() ? null : `${label} is required.`;

export const email: Validator = (value) =>
  !value.trim()
    ? 'Work email is required.'
    : EMAIL_RE.test(value.trim())
      ? null
      : 'Enter a valid work email address (name@company.com).';

export const minLength =
  (label: string, length: number): Validator =>
  (value) =>
    value.length >= length ? null : `${label} must be at least ${length} characters.`;

export interface PasswordRule {
  label: string;
  test: (value: string) => boolean;
}

export const passwordRules: PasswordRule[] = [
  { label: 'At least 12 characters', test: (v) => v.length >= 12 },
  { label: 'A lowercase and an uppercase letter', test: (v) => /[a-z]/.test(v) && /[A-Z]/.test(v) },
  { label: 'A number or symbol', test: (v) => /[0-9\W]/.test(v) },
];

export const password: Validator = (value) => {
  if (!value) return 'Password is required.';
  const failed = passwordRules.filter((rule) => !rule.test(value));
  if (failed.length === 0) return null;
  return `Password needs: ${failed.map((r) => r.label.toLowerCase()).join('; ')}.`;
};

export function runValidators(
  fields: Record<string, Validator[]>,
  form: Record<string, string>,
): Record<string, string> {
  const errors: Record<string, string> = {};
  for (const [name, validators] of Object.entries(fields)) {
    for (const validate of validators) {
      const message = validate(form[name] ?? '', form);
      if (message) {
        errors[name] = message;
        break;
      }
    }
  }
  return errors;
}
