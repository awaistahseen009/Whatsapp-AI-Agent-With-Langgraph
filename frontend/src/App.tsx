import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import DashboardLayout from './layouts/DashboardLayout';
import LoginPage from './pages/LoginPage';
import DashboardOverview from './pages/DashboardOverview';
import ClientsPage from './pages/ClientsPage';
import ChatSessionsPage from './pages/ChatSessionsPage';
import PropertiesPage from './pages/PropertiesPage';
import MeetingsPage from './pages/MeetingsPage';
import EscalationsPage from './pages/EscalationsPage';
import NotFoundPage from './pages/NotFoundPage';

// Protect routes based on authentication
const ProtectedRoute = ({ children, requiredRole }: { children: React.ReactNode, requiredRole?: 'owner' | 'agent' }) => {
  const { user, isLoading } = useAuth();
  
  if (isLoading) {
    return <div className="h-screen w-screen flex items-center justify-center bg-cream-50 text-anthropic-light">Loading...</div>;
  }
  
  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (requiredRole && user.role !== requiredRole) {
    // If agent tries to access owner route, kick them back to dashboard
    return <Navigate to="/" replace />;
  }
  
  return <>{children}</>;
};

function AppRoutes() {
  return (
    <Routes>
      {/* Public */}
      <Route path="/login" element={<LoginPage />} />
      
      {/* Protected Dashboard */}
      <Route path="/" element={<ProtectedRoute><DashboardLayout /></ProtectedRoute>}>
        <Route index element={<DashboardOverview />} />
        <Route path="clients" element={<ClientsPage />} />
        <Route path="sessions" element={<ChatSessionsPage />} />
        <Route path="properties" element={<PropertiesPage />} />
        <Route path="meetings" element={<MeetingsPage />} />
        <Route path="escalations" element={<EscalationsPage />} />
      </Route>

      {/* 404 Not Found Fallback */}
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
