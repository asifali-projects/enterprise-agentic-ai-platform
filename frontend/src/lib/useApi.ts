import { useCallback, useEffect, useState } from 'react';
import { ApiError, request, type RequestOptions } from './api';
import { useAuth } from './auth';

interface QueryState<T> {
  data: T | null;
  error: string | null;
  loading: boolean;
  reload: () => void;
}

/** Authenticated GET with loading / error / refetch state. */
export function useQuery<T>(path: string | null): QueryState<T> {
  const { token, logout } = useAuth();
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(Boolean(path));
  const [nonce, setNonce] = useState(0);

  useEffect(() => {
    if (!path) {
      setData(null);
      setLoading(false);
      return;
    }
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    request<T>(path, { token, signal: controller.signal })
      .then((result) => setData(result))
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        if (err instanceof ApiError && err.isAuthError) {
          logout('expired');
          return;
        }
        setError(err instanceof Error ? err.message : 'Unable to load data.');
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [path, token, nonce, logout]);

  const reload = useCallback(() => setNonce((value) => value + 1), []);
  return { data, error, loading, reload };
}

/** Authenticated mutation helper. Routes 401s through logout. */
export function useMutation() {
  const { token, logout } = useAuth();
  const [pending, setPending] = useState(false);

  const mutate = useCallback(
    async <T,>(path: string, options: Omit<RequestOptions, 'token'> = {}): Promise<T> => {
      setPending(true);
      try {
        return await request<T>(path, { ...options, token });
      } catch (error) {
        if (error instanceof ApiError && error.isAuthError) logout('expired');
        throw error;
      } finally {
        setPending(false);
      }
    },
    [token, logout],
  );

  return { mutate, pending };
}
