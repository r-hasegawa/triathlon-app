import React from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { AdminDashboard } from './AdminDashboard';
import { UserDashboard } from './UserDashboard';
import { Layout } from '@/components/layout/Layout';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

export const Dashboard: React.FC = () => {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <Layout>
        <div className="flex justify-center items-center h-64">
          <LoadingSpinner size="lg" />
        </div>
      </Layout>
    );
  }

  const isAdmin = user && 'admin_id' in user;

  // 管理者の場合は管理者ダッシュボードを表示
  if (isAdmin) {
    return <AdminDashboard />;
  }

  // 被験者の場合は被験者ダッシュボードを表示
  return <UserDashboard />;
};