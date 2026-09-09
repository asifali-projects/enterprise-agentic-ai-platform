/** Presentation helpers shared across pages. */

export function formatDateTime(value?: string | null): string {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function formatRelative(value?: string | null): string {
  if (!value) return '—';
  const then = new Date(value).getTime();
  if (Number.isNaN(then)) return value;
  const seconds = Math.round((Date.now() - then) / 1000);
  const ranges: [number, Intl.RelativeTimeFormatUnit][] = [
    [60, 'second'],
    [3600, 'minute'],
    [86400, 'hour'],
    [604800, 'day'],
    [2629800, 'week'],
    [31557600, 'month'],
    [Number.POSITIVE_INFINITY, 'year'],
  ];
  const formatter = new Intl.RelativeTimeFormat(undefined, { numeric: 'auto' });
  let previous = 1;
  for (const [limit, unit] of ranges) {
    if (Math.abs(seconds) < limit) {
      return formatter.format(-Math.round(seconds / previous), unit);
    }
    previous = limit;
  }
  return value;
}

export function titleCase(value: string): string {
  return value.replace(/[_-]+/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

export function shortId(value?: string | null): string {
  return value ? value.slice(0, 8) : '—';
}
