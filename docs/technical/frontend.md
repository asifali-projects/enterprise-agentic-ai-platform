# Frontend guide

A React 19 + TypeScript single-page control plane built with Vite and served in
production as static files behind Nginx.

## Layout

```
frontend/src/
  main.tsx                 mounts providers: ErrorBoundary > BrowserRouter > ToastProvider > AuthProvider
  App.tsx                  route table + <RequireAuth> guard
  styles.css               design-system tokens and component styles
  lib/
    api.ts                 typed fetch client + ApiError (parses the FastAPI error envelope)
    auth.tsx               AuthProvider / useAuth — token persistence, /me bootstrap, login/register/demo/logout
    useApi.ts              useQuery (loading/error/reload) and useMutation (401 → logout)
    validation.ts          field validators with specific, professional messages
    rbac.ts                capability matrix mirrored from the backend (UI hint only)
    types.ts               shared API response types
    format.ts, ws.ts       date formatting, run-events socket URL
  components/
    AppShell.tsx           sidebar + top bar, grouped RBAC-aware navigation
    Toast.tsx              non-blocking success/error/info notifications
    ErrorBoundary.tsx      full-page fallback for unhandled render errors
    ProjectPicker.tsx      shared project selector (auto-selects when there is one project)
    ui.tsx                 Button, Field, SelectField, TextAreaField, LoadingBlock,
                           EmptyState, ErrorState, Panel, StatusBadge, DataTable, Drawer
  pages/                   one component per route
```

## Authentication and redirect flow

`AuthProvider` holds `{ status, user, token }` where `status` is
`loading | authenticated | anonymous`.

- On mount, if a token is in `localStorage` (`eaiop.token`), it calls
  `GET /api/v1/me`. Success → `authenticated`; a 401 → the token is cleared.
- `login` / `register` / `startDemo` POST to the API, store the returned
  `access_token`, then **await** `GET /api/v1/me` before resolving. Only then
  does `AuthPage` call `navigate(redirectTo)`.
- `redirectTo` is the path the user originally requested (captured by
  `<RequireAuth>` in router `state.from`) or `/overview`.
- Any API call that returns 401 (via `useQuery` / `useMutation`) triggers
  `logout()`, which routes back to `/login`.

This is the fix for the previous build, where registration succeeded but the
app called a non-existent `/api/v1/auth/me` and never left the login screen.

## Validation and messages

- **Client-side:** `lib/validation.ts` checks required fields, email format and
  a three-rule password policy (shown as a live checklist on the sign-up form).
  Submit is blocked and inline field errors are shown until the form is valid.
- **Server-side:** `lib/api.ts` converts `{ detail: [...] }` validation arrays
  into friendly per-field messages and a form-level summary; string `detail`
  values become the toast/message text. Status codes map to sensible defaults
  ("Your session has expired…", "You do not have permission…", etc.).
- **Feedback:** every mutation shows a `Toast` — a titled success line with a
  short description, or an error toast with the API message.

## State and data

- No global store. `useQuery(path)` fetches on mount and on `reload()`, with
  `loading` / `error` states rendered as `LoadingBlock` / `ErrorState`.
- Long-running runs: the run drawer opens a `WebSocket` to
  `/ws/runs/{id}` and appends live events on top of the persisted history from
  `GET /api/v1/runs/{id}/events`.

## Design system

`styles.css` defines CSS custom properties for colour, radius and typography and
a small set of BEM-ish component classes. The theme is a single dark palette;
all colours are declared on `:root`. Layout is responsive (sidebar collapses to
a two-column nav under 820px; the auth screen stacks under 1000px).

## Build

```bash
cd frontend
npm install
npm run typecheck      # tsc --noEmit
npm run build          # tsc --noEmit && vite build  → dist/
npm run dev            # Vite dev server on :5173
```

### API origin

The SPA calls the API on **its own origin** (`/api/...`, `/ws/...`). In
production, Nginx (`frontend/nginx.conf`) proxies those paths to the `api`
service; in `npm run dev`, the Vite dev server proxies them to
`VITE_DEV_API_TARGET` (default `http://localhost:8000`). This removes
cross-origin/CORS, mixed-content and `localhost` name-resolution failure modes
in the browser.

Set `VITE_API_URL` at build time only if the API must be reached at a different
origin than the page. No secrets are ever placed in the bundle.
