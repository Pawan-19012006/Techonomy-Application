import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'sonner';

import { ThemeProvider } from './contexts/ThemeContext';
import { AuthProvider, useAuth } from './contexts/AuthContext';

import { AppLayout } from './components/layouts/AppLayout';
import { ProtectedRoute } from './components/common/ProtectedRoute';
import { AdminLayout } from './components/layouts/AdminLayout';

import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { DocumentsPage } from './pages/DocumentsPage';
import { DocumentViewerPage } from './pages/DocumentViewerPage';
import { KnowledgeAssistantPage } from './pages/KnowledgeAssistantPage';
import { RulesPage } from './pages/RulesPage';
import { AdminOverviewPage } from './pages/admin/AdminOverviewPage';
import { AdminTeamDetailPage } from './pages/admin/AdminTeamDetailPage';
import { NotFoundPage } from './pages/NotFoundPage';

const ProtectedAdminRoute: React.FC = () => {
  const { isAdminAuthenticated } = useAuth();
  if (!isAdminAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return <Outlet />;
};

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AuthProvider>
          <Toaster position="top-right" richColors closeButton />
          <BrowserRouter>
            <Routes>
              {/* Public Route */}
              <Route path="/login" element={<LoginPage />} />

              {/* Protected Participant Routes */}
              <Route element={<ProtectedRoute />}>
                <Route element={<AppLayout />}>
                  <Route path="/" element={<Navigate to="/dashboard" replace />} />
                  <Route path="/dashboard" element={<DashboardPage />} />
                  <Route path="/documents" element={<DocumentsPage />} />
                  <Route path="/documents/:docId" element={<DocumentViewerPage />} />
                  <Route path="/assistant" element={<KnowledgeAssistantPage />} />
                  <Route path="/rules" element={<RulesPage />} />
                </Route>
              </Route>

              {/* Protected Admin Control Panel Routes */}
              <Route element={<ProtectedAdminRoute />}>
                <Route element={<AdminLayout />}>
                  <Route path="/admin" element={<AdminOverviewPage />} />
                  <Route path="/admin/teams/:teamName" element={<AdminTeamDetailPage />} />
                  <Route path="/admin/documents" element={<DocumentsPage />} />
                  <Route path="/admin/documents/:docId" element={<DocumentViewerPage />} />
                </Route>
              </Route>

              {/* 404 Catch-all */}
              <Route path="*" element={<NotFoundPage />} />
            </Routes>
          </BrowserRouter>
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
};

export default App;
