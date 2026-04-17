import React, { useMemo } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { ThemeProvider, CssBaseline, Box } from '@mui/material';
import { ErrorBoundary } from 'react-error-boundary';
import { createAppTheme, DEFAULT_BG, DEFAULT_PAPER } from './theme/theme';
import { AuthContextProvider } from './components/context_providers/AuthContext';
import { UserContextProvider } from './components/context_providers/UserContext';
import { NotificationProvider } from './components/context_providers/NotificationContext';
import { ThemeConfigProvider, useThemeConfig } from './components/context_providers/ThemeConfigContext';
import { OrganizationContextProvider } from './components/context_providers/OrganizationContext';
import { DocumentContextProvider } from './components/context_providers/DocumentContext';
import ProtectedRoute from './components/shared/ProtectedRoute';
import { useAuth } from './components/context_providers/AuthContext';

// Public pages
import HomePage from './components/pages/HomePage';
import LoginPage from './components/pages/LoginPage';
import RegisterPage from './components/pages/RegisterPage';
import ForgotPasswordPage from './components/pages/ForgotPasswordPage';
import ResetPasswordPage from './components/pages/ResetPasswordPage';
import ForceResetPasswordPage from './components/pages/ForceResetPasswordPage';
import PricingPage from './components/pages/PricingPage';
import OAuthCallbackPage from './components/pages/OAuthCallbackPage';
import AcceptInvitationPage from './components/pages/AcceptInvitationPage';
import VerifyEmailPage from './components/pages/VerifyEmailPage';

// App pages
import DashboardPage from './components/pages/DashboardPage';
import DocumentsPage from './components/pages/DocumentsPage';
import ModelsPage from './components/pages/ModelsPage';
import PipelinesPage from './components/pages/PipelinesPage';
import PipelineDetailPage from './components/pages/PipelineDetailPage';
import OutputsPage from './components/pages/OutputsPage';
import OrgSettingsPage from './components/pages/OrgSettingsPage';
import PersonalSettingsPage from './components/pages/PersonalSettingsPage';
import OrgSetupWizard from './components/pages/OrgSetupWizard';
import OrganizationsPage from './components/pages/OrganizationsPage';

import AppLayout from './components/shared/AppLayout';
import PublicLayout from './components/shared/PublicLayout';
import './App.css';

/** Redirects authenticated users to the dashboard */
const SmartRedirect: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  return <Navigate to="/dashboard" replace />;
};

const ErrorFallback: React.FC<{ error: Error }> = ({ error }) => (
  <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', p: 3, textAlign: 'center' }}>
    <h1>Oops! Something went wrong</h1>
    <p>{error.message}</p>
    <button onClick={() => window.location.reload()}>Reload Page</button>
  </Box>
);

const ThemedApp: React.FC = () => {
  const { config } = useThemeConfig();
  const theme = useMemo(
    () => createAppTheme(
      config.colors.primary,
      config.colors.secondary,
      config.colors.background || DEFAULT_BG,
      config.colors.paper || DEFAULT_PAPER,
    ),
    [config.colors.primary, config.colors.secondary, config.colors.background, config.colors.paper]
  );

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <NotificationProvider>
        <ErrorBoundary FallbackComponent={ErrorFallback}>
          <AuthContextProvider>
            <UserContextProvider>
            <OrganizationContextProvider>
            <DocumentContextProvider>
              <BrowserRouter basename="/">
                <Routes>
                  {/* Public routes (with public header) */}
                  <Route element={<PublicLayout />}>
                    <Route path="/" element={<HomePage />} />
                    <Route path="/pricing" element={<PricingPage />} />
                    <Route path="/login" element={<LoginPage />} />
                    <Route path="/register" element={<RegisterPage />} />
                    <Route path="/forgot-password" element={<ForgotPasswordPage />} />
                    <Route path="/reset-password/:token" element={<ResetPasswordPage />} />
                    <Route path="/force-reset-password" element={<ForceResetPasswordPage />} />
                    <Route path="/verify-email" element={<VerifyEmailPage />} />
                  </Route>
                  <Route path="/auth/callback/:provider" element={<OAuthCallbackPage />} />
                  <Route path="/accept-invitation/:token" element={<AcceptInvitationPage />} />

                  {/* Org setup */}
                  <Route path="/setup" element={<ProtectedRoute><OrgSetupWizard /></ProtectedRoute>} />

                  {/* App routes (with layout) */}
                  <Route element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
                    <Route path="/dashboard" element={<DashboardPage />} />
                    <Route path="/documents" element={<DocumentsPage />} />
                    <Route path="/models" element={<ModelsPage />} />
                    <Route path="/pipelines" element={<PipelinesPage />} />
                    <Route path="/pipelines/:id" element={<PipelineDetailPage />} />
                    <Route path="/outputs" element={<OutputsPage />} />
                    <Route path="/org/settings" element={<OrgSettingsPage />} />
                    <Route path="/settings" element={<PersonalSettingsPage />} />
                    <Route path="/organizations" element={<OrganizationsPage />} />
                  </Route>

                  {/* Catch-all: route to dashboard */}
                  <Route path="*" element={<SmartRedirect />} />
                </Routes>
              </BrowserRouter>
            </DocumentContextProvider>
            </OrganizationContextProvider>
            </UserContextProvider>
          </AuthContextProvider>
        </ErrorBoundary>
      </NotificationProvider>
    </ThemeProvider>
  );
};

function App() {
  return (
    <ThemeConfigProvider>
      <ThemedApp />
    </ThemeConfigProvider>
  );
}

export default App;
