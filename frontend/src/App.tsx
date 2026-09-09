import type { ReactElement } from 'react';
import { Navigate, Route, Routes, useLocation } from 'react-router-dom';
import { AppShell } from './components/AppShell';
import { LoadingBlock } from './components/ui';
import { useAuth } from './lib/auth';
import { AuthPage } from './pages/AuthPage';
import { Overview } from './pages/Overview';
import { Projects } from './pages/Projects';
import { Agents } from './pages/Agents';
import { Tools } from './pages/Tools';
import { Workflows } from './pages/Workflows';
import { Runs } from './pages/Runs';
import { Approvals } from './pages/Approvals';
import { Evaluations } from './pages/Evaluations';
import { Memory } from './pages/Memory';
import { AuditLog } from './pages/AuditLog';
import { Team } from './pages/Team';
import { Governance } from './pages/Governance';
import { Protocols } from './pages/Protocols';
import { Observability } from './pages/Observability';
import { NotFound } from './pages/NotFound';

function RequireAuth({ children }: { children: ReactElement }) {
  const { status } = useAuth();
  const location = useLocation();
  if (status === 'loading') {
    return (
      <div className="fullscreen-center">
        <LoadingBlock label="Restoring your session…" />
      </div>
    );
  }
  if (status !== 'authenticated') {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  return children;
}

export function App() {
  const { status } = useAuth();

  return (
    <Routes>
      <Route
        path="/login"
        element={status === 'authenticated' ? <Navigate to="/overview" replace /> : <AuthPage />}
      />
      <Route
        element={
          <RequireAuth>
            <AppShell />
          </RequireAuth>
        }
      >
        <Route path="/overview" element={<Overview />} />
        <Route path="/projects" element={<Projects />} />
        <Route path="/agents" element={<Agents />} />
        <Route path="/tools" element={<Tools />} />
        <Route path="/workflows" element={<Workflows />} />
        <Route path="/runs" element={<Runs />} />
        <Route path="/approvals" element={<Approvals />} />
        <Route path="/evaluations" element={<Evaluations />} />
        <Route path="/memory" element={<Memory />} />
        <Route path="/audit" element={<AuditLog />} />
        <Route path="/team" element={<Team />} />
        <Route path="/governance" element={<Governance />} />
        <Route path="/protocols" element={<Protocols />} />
        <Route path="/observability" element={<Observability />} />
      </Route>
      <Route path="/" element={<Navigate to="/overview" replace />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
