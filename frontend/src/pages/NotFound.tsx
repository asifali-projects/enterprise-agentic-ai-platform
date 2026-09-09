import { Link } from 'react-router-dom';

export function NotFound() {
  return (
    <div className="fullscreen-center">
      <div className="state state--empty">
        <p className="state__title">Page not found</p>
        <p className="state__description">The page you requested does not exist in the console.</p>
        <Link className="btn btn--primary" to="/overview">
          Back to overview
        </Link>
      </div>
    </div>
  );
}
