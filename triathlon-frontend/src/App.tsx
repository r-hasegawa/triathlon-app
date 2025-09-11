import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from '@/contexts/AuthContext';
import { Login } from '@/pages/Login';
import { Dashboard } from '@/pages/Dashboard';
import { DataDetail } from '@/pages/DataDetail';
import { CSVUpload } from '@/pages/CSVUpload';
import { CompetitionManagement } from '@/pages/CompetitionManagement';
import { UploadHistory } from '@/pages/UploadHistory';
import { UserManagement } from '@/pages/UserManagement';
import { MultiSensorUpload } from '@/pages/MultiSensorUpload';
import { MultiSensorStatus } from '@/pages/MultiSensorStatus';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';

// 🆕 新しいページを追加
import { SensorDataUpload } from '@/pages/SensorDataUpload';

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
            element={isAuthenticated ? 
              <Navigate to="/dashboard" replace /> : <Login />} 
          />
          
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />

          {/* データ詳細ページ */}
          <Route
            path="/data/:id"
            element={
              <ProtectedRoute>
                <DataDetail />
              </ProtectedRoute>
            }
          />

          {/* CSVアップロード */}
          <Route
            path="/upload"
            element={
              <ProtectedRoute>
                <CSVUpload />
              </ProtectedRoute>
            }
          />

          {/* アップロード履歴 */}
          <Route
            path="/history"
            element={
              <ProtectedRoute>
                <UploadHistory />
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

          <Route 
            path="/admin/competitions" 
            element={
              <AdminRoute>
                <CompetitionManagement />
              </AdminRoute>
            }
          />

          {/* マルチセンサー機能 */}
          <Route 
            path="/multi-sensor/upload" 
            element={
              <AdminRoute>
                <MultiSensorUpload />
              </AdminRoute>
            } 
          />
          
          <Route 
            path="/multi-sensor/status" 
            element={
              <AdminRoute>
                <MultiSensorStatus />
              </AdminRoute>
            } 
          />

          {/* 🆕 新しい実データ対応アップロード画面 */}
          <Route
            path="/sensor-data-upload" 
            element={
              <AdminRoute>
                <SensorDataUpload />
              </AdminRoute>
            } 
          />

          {/* 🔄 従来の管理者マルチセンサー（互換性維持） */}
          <Route
            path="/admin/multi-sensor" 
            element={
              <AdminRoute>
                <MultiSensorUpload />
              </AdminRoute>
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