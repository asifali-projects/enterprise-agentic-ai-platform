/**
 * Typed API client for the Enterprise Agentic AI control plane.
 *
 * - Reads the API base URL from VITE_API_URL (never a secret).
 * - Normalises the FastAPI error envelope ({ detail: string | ValidationError[] })
 *   into a single human-readable message plus per-field errors for forms.
 * - Surfaces authentication failures so the auth layer can end the session.
 */

// Default: same origin as the SPA. In production Nginx proxies /api and /ws to
// the API service, so there is no cross-origin request from the browser. Set
// VITE_API_URL only when the API is served from a different origin (e.g. running
// the Vite dev server directly against a remote API).
export const API_BASE_URL: string =
  (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, '') ?? '';

export type FieldErrors = Record<string, string>;

export class ApiError extends Error {
  status: number;
  fieldErrors: FieldErrors;
  constructor(message: string, status: number, fieldErrors: FieldErrors = {}) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.fieldErrors = fieldErrors;
  }
  get isAuthError(): boolean {
    return this.status === 401;
  }
}

type ValidationItem = { loc: (string | number)[]; msg: string };

function parseErrorBody(status: number, body: unknown): ApiError {
  if (body && typeof body === 'object' && 'detail' in body) {
    const detail = (body as { detail: unknown }).detail;
    if (typeof detail === 'string') {
      return new ApiError(detail, status);
    }
    if (Array.isArray(detail)) {
      const fieldErrors: FieldErrors = {};
      const messages: string[] = [];
      for (const item of detail as ValidationItem[]) {
        const field = String(item.loc?.[item.loc.length - 1] ?? '');
        const message = friendlyValidationMessage(field, item.msg);
        if (field && field !== 'body') fieldErrors[field] = message;
        messages.push(message);
      }
      return new ApiError(messages[0] || 'The request could not be validated.', status, fieldErrors);
    }
  }
  return new ApiError(defaultMessageForStatus(status), status);
}

function friendlyValidationMessage(field: string, raw: string): string {
  const label = field ? field.replace(/_/g, ' ').replace(/^\w/, (c) => c.toUpperCase()) : 'Value';
  if (raw.includes('valid email')) return 'Enter a valid work email address.';
  if (raw.includes('at least') && raw.includes('character')) {
    const match = raw.match(/at least (\d+)/);
    return `${label} must be at least ${match?.[1] ?? 'the required number of'} characters.`;
  }
  if (raw.includes('Field required')) return `${label} is required.`;
  return `${label}: ${raw}`;
}

function defaultMessageForStatus(status: number): string {
  if (status === 401) return 'Your session has expired. Please sign in again.';
  if (status === 403) return 'You do not have permission to perform this action.';
  if (status === 404) return 'The requested resource was not found.';
  if (status === 409) return 'That action conflicts with the current state.';
  if (status >= 500) return 'The service is temporarily unavailable. Please try again.';
  return 'The request could not be completed.';
}

export interface RequestOptions {
  method?: string;
  body?: unknown;
  token?: string | null;
  signal?: AbortSignal;
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, token, signal } = options;
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      signal,
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch (error) {
    if ((error as Error).name === 'AbortError') throw error;
    throw new ApiError('Cannot reach the API. Confirm the service is running and try again.', 0);
  }

  if (response.status === 204) return undefined as T;

  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    throw parseErrorBody(response.status, payload);
  }
  return payload as T;
}
