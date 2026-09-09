import { Component, type ErrorInfo, type ReactNode } from 'react';

interface Props {
  children: ReactNode;
}
interface State {
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    // Kept intentionally minimal: production telemetry is emitted server-side.
    console.error('Unhandled UI error', error, info.componentStack);
  }

  render() {
    if (this.state.error) {
      return (
        <div className="app-crash">
          <div className="app-crash__card">
            <h1>The console hit an unexpected error</h1>
            <p>
              The last action could not be completed. Reload the page to continue; if the problem
              persists, contact your platform administrator.
            </p>
            <button className="btn btn--primary" onClick={() => window.location.reload()}>
              Reload console
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
