import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';

const APP_TITLE = 'ToStructured AI';

const ROUTE_TITLES: Record<string, string> = {
  '/dashboard': 'Dashboard',
  '/documents': 'Documents',
  '/models': 'Models',
  '/pipelines': 'Pipelines',
  '/outputs': 'Outputs',
  '/organizations': 'Organizations',
  '/settings': 'Settings',
};

export const useBrowserTitle = (): void => {
  const location = useLocation();

  useEffect(() => {
    const matchedRoute = Object.entries(ROUTE_TITLES).find(
      ([path]) => location.pathname === path || location.pathname.startsWith(path + '/')
    );

    document.title = matchedRoute
      ? `${matchedRoute[1]} - ${APP_TITLE}`
      : APP_TITLE;

    return () => {
      document.title = APP_TITLE;
    };
  }, [location.pathname]);
};
