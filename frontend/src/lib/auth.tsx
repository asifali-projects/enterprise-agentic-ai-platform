import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import { ApiError, request } from './api';

export interface Organization {
  id: string;
  name: string;
  slug: string;
  is_demo: boolean;
}

export interface CurrentUser {
  id: string;
  full_name: string;
  email: string;
  role: string;
  organization: Organization | null;
}

interface Credentials {
  email: string;
  password: string;
}

interface RegistrationInput {
  full_name: string;
  email: string;
  password: string;
  organization_name: string;
}

interface DemoInput {
  organization_name?: string;
  full_name?: string;
}

interface AuthState {
  status: 'loading' | 'authenticated' | 'anonymous';
  user: CurrentUser | null;
  token: string | null;
  login: (credentials: Credentials) => Promise<void>;
  register: (input: RegistrationInput) => Promise<void>;
  startDemo: (input: DemoInput) => Promise<void>;
  logout: (reason?: string) => void;
}

const STORAGE_KEY = 'eaiop.token';
const AuthContext = createContext<AuthState | null>(null);

function readToken(): string | null {
  try {
    return window.localStorage.getItem(STORAGE_KEY);
  } catch {
    return null;
  }
}

function persistToken(token: string | null) {
  try {
    if (token) window.localStorage.setItem(STORAGE_KEY, token);
    else window.localStorage.removeItem(STORAGE_KEY);
  } catch {
    /* storage unavailable — session lives in memory only */
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => readToken());
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [status, setStatus] = useState<AuthState['status']>(token ? 'loading' : 'anonymous');

  const applyToken = useCallback(async (nextToken: string) => {
    persistToken(nextToken);
    setToken(nextToken);
    const profile = await request<CurrentUser>('/api/v1/me', { token: nextToken });
    setUser(profile);
    setStatus('authenticated');
  }, []);

  const logout = useCallback((_reason?: string) => {
    persistToken(null);
    setToken(null);
    setUser(null);
    setStatus('anonymous');
  }, []);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    request<CurrentUser>('/api/v1/me', { token })
      .then((profile) => {
        if (cancelled) return;
        setUser(profile);
        setStatus('authenticated');
      })
      .catch((error) => {
        if (cancelled) return;
        if (error instanceof ApiError && !error.isAuthError) {
          // Transient failure — keep the token, report unauthenticated for now.
          setStatus('anonymous');
        } else {
          logout('expired');
        }
      });
    return () => {
      cancelled = true;
    };
    // Runs once on mount for the persisted token.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const login = useCallback(
    async (credentials: Credentials) => {
      const { access_token } = await request<{ access_token: string }>('/api/v1/login', {
        method: 'POST',
        body: credentials,
      });
      await applyToken(access_token);
    },
    [applyToken],
  );

  const register = useCallback(
    async (input: RegistrationInput) => {
      const { access_token } = await request<{ access_token: string }>('/api/v1/register', {
        method: 'POST',
        body: input,
      });
      await applyToken(access_token);
    },
    [applyToken],
  );

  const startDemo = useCallback(
    async (input: DemoInput) => {
      const { access_token } = await request<{ access_token: string }>('/api/v1/demo', {
        method: 'POST',
        body: {
          organization_name: input.organization_name || 'Demo Organization',
          full_name: input.full_name || 'Demo Operator',
        },
      });
      await applyToken(access_token);
    },
    [applyToken],
  );

  const value = useMemo<AuthState>(
    () => ({ status, user, token, login, register, startDemo, logout }),
    [status, user, token, login, register, startDemo, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used inside an AuthProvider');
  return context;
}
