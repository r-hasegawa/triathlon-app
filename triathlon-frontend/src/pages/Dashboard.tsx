import React from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { AdminDashboard } from './AdminDashboard';
import { UserDashboard } from './UserDashboard';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

export const Dashboard: React.FC = () => {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex justify-center items-center">
        <LoadingSpinner size="lg" text="ダッシュボードを読み込んでいます..." />
      </div>
    );
  }

  // 管理者かどうかを判定
  const isAdmin = user && 'admin_id' in user;

  return isAdmin ? <AdminDashboard /> : <UserDashboard />;
};