import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../lib/auth';
import { titleCase } from '../lib/format';

interface NavItem {
  to: string;
  label: string;
  group: string;
}

const NAV: NavItem[] = [
  { to: '/overview', label: 'Overview', group: 'Operate' },
  { to: '/projects', label: 'Projects', group: 'Operate' },
  { to: '/agents', label: 'Agents', group: 'Build' },
  { to: '/tools', label: 'Tools', group: 'Build' },
  { to: '/workflows', label: 'Workflows', group: 'Build' },
  { to: '/runs', label: 'Runs', group: 'Execute' },
  { to: '/approvals', label: 'Approvals', group: 'Execute' },
  { to: '/evaluations', label: 'Evaluations', group: 'Assure' },
  { to: '/memory', label: 'Memory', group: 'Assure' },
  { to: '/audit', label: 'Audit log', group: 'Govern' },
  { to: '/team', label: 'Team & roles', group: 'Govern' },
  { to: '/governance', label: 'Policies', group: 'Govern' },
  { to: '/protocols', label: 'MCP / A2A', group: 'Integrate' },
  { to: '/observability', label: 'Observability', group: 'Integrate' },
];

export function AppShell() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const groups = [...new Set(NAV.map((item) => item.group))];
  const active = NAV.find((item) => location.pathname.startsWith(item.to));

  return (
    <div className="shell">
      <aside className="shell__sidebar">
        <div className="shell__brand">
          <span className="shell__mark">EA</span>
          <span>Agentic Control Plane</span>
        </div>
        <div className="shell__org">
          <strong>{user?.organization?.name ?? 'Organization'}</strong>
          <span>
            {titleCase(user?.role ?? 'member')} ·{' '}
            {user?.organization?.is_demo ? 'Demo tenant' : 'Live tenant'}
          </span>
        </div>
        <nav className="shell__nav">
          {groups.map((group) => (
            <div key={group} className="shell__nav-group">
              <p className="shell__nav-heading">{group}</p>
              {NAV.filter((item) => item.group === group).map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    `shell__nav-link ${isActive ? 'shell__nav-link--active' : ''}`
                  }
                >
                  {item.label}
                </NavLink>
              ))}
            </div>
          ))}
        </nav>
        <button className="shell__signout" onClick={() => logout()}>
          Sign out
        </button>
      </aside>

      <div className="shell__main">
        <header className="shell__topbar">
          <div>
            <p className="eyebrow">Control plane</p>
            <h1>{active?.label ?? 'Overview'}</h1>
          </div>
          <div className="shell__identity">
            <span className="shell__identity-name">{user?.full_name}</span>
            <span className="shell__identity-mail">{user?.email}</span>
          </div>
        </header>
        <main className="shell__content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
