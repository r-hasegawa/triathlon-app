import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from '@/contexts/AuthContext';
import { Login } from '@/pages/Login';
import { Dashboard } from '@/pages/Dashboard';
import { CompetitionManagement } from '@/pages/CompetitionManagement';
import { UserManagement } from '@/pages/UserManagement';
import { UserDetail } from '@/pages/UserDetail';
import SensorDataUpload from '@/pages/SensorDataUpload';
import AdminPasswordChange from '@/pages/AdminPasswordChange';
import UserPasswordChange from '@/pages/UserPasswordChange';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';

// スタイルインポート
import '@/styles/globals.css';

// 認証が必要なルートを保護するコンポーネント
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex justify-center items-center">
        <LoadingSpinner size="lg" text="認証確認中..." />
      </div>
    );
  }

  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />;
};

// 管理者専用ルートを保護するコンポーネント
const AdminRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex justify-center items-center">
        <LoadingSpinner size="lg" text="権限確認中..." />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  const isAdmin = user && 'admin_id' in user;
  if (!isAdmin) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
};

// アプリのメインコンポーネント
const AppRoutes: React.FC = () => {
  const { isAuthenticated } = useAuth();

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-gray-50">
        <Routes>
          <Route 
            path="/login" 
            element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <Login />} 
          />
          
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />

          {/* 一般ユーザー向けルート */}
          <Route
            path="/my-data"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />

          {/* 管理者専用ルート */}
          <Route
            path="/admin/users"
            element={
              <AdminRoute>
                <UserManagement />
              </AdminRoute>
            }
          />

          {/* ユーザー詳細ページ（管理者が他のユーザーの詳細を見る） */}
          <Route
            path="/admin/users/:userId"
            element={
              <AdminRoute>
                <UserDetail />
              </AdminRoute>
            }
          />

          <Route 
            path="/admin/competitions" 
            element={
              <AdminRoute>
                <CompetitionManagement />
              </AdminRoute>
            }
          />

          {/* データアップロード画面 */}
          <Route
            path="/admin/upload" 
            element={
              <AdminRoute>
                <SensorDataUpload />
              </AdminRoute>
            } 
          />

          {/* 管理者パスワード変更ページ（管理者専用） */}
          <Route
            path="/admin/change-credentials"
            element={
              <AdminRoute>
                <AdminPasswordChange />
              </AdminRoute>
            }
          />

          {/* ユーザーパスワード変更ページ（一般ユーザー用） */}
          <Route
            path="/user/change-credentials"
            element={
              <ProtectedRoute>
                <UserPasswordChange />
              </ProtectedRoute>
            }
          />
          
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </div>
    </ErrorBoundary>
  );
};

function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <Router>
          <AppRoutes />
        </Router>
      </AuthProvider>
    </ErrorBoundary>
  );
}

export default App;