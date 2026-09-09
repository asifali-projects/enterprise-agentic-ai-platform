import { API_BASE_URL } from './api';

export function runEventsSocketUrl(runId: string): string {
  // When API_BASE_URL is empty the API is same-origin (Nginx proxies /ws);
  // otherwise derive the ws origin from the configured API base.
  const origin = API_BASE_URL || window.location.origin;
  const base = origin.replace(/^http/, 'ws');
  return `${base}/ws/runs/${runId}`;
}
