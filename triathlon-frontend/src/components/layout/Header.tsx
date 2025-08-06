import React from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/Button';

export const Header: React.FC = () => {
  const { user, logout, isAuthenticated } = useAuth();

  if (!isAuthenticated || !user) {
    return null;
  }

  const isAdmin = 'admin_id' in user;

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center">
            <h1 className="text-xl font-semibold text-gray-900">
              トライアスロンセンサデータシステム
            </h1>
            {isAdmin && (
              <span className="ml-3 px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded-full">
                管理者
              </span>
            )}
          </div>
          
          <div className="flex items-center space-x-4">
            <div className="text-sm text-gray-700">
              <span className="font-medium">{user.full_name || user.username}</span>
              {isAdmin && <span className="ml-1 text-gray-500">({user.role})</span>}
            </div>
            
            <Button
              variant="outline"
              size="sm"
              onClick={logout}
            >
              ログアウト
            </Button>
          </div>
        </div>
      </div>
    </header>
  );
};