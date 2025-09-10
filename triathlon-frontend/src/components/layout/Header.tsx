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
    <header className="sticky top-0 z-40 border-b border-gray-200 bg-white shadow-sm">
      {/* フルワイドコンテナ */}
      <div className="w-full px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          
          {/* ロゴ・タイトル部分 */}
          <div className="flex items-center flex-shrink-0">
            <div className="flex items-center">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary-600 mr-4">
                <svg className="h-5 w-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              
              {/* レスポンシブタイトル */}
              <div className="flex flex-col mr-4">
                <h1 className="hidden sm:block text-lg lg:text-xl font-bold text-gray-900 leading-tight">
                  トライアスロンセンサデータシステム
                </h1>
                <h1 className="block sm:hidden text-base font-bold text-gray-900">
                  センサデータシステム
                </h1>
              </div>
            </div>
            
            {/* 管理者バッジ */}
            {isAdmin && (
              <span className="badge badge-primary hidden sm:inline-flex">
                管理者
              </span>
            )}
          </div>
          
          {/* ユーザー情報・ログアウト部分 */}
          <div className="flex items-center gap-4 flex-shrink-0">
            
            {/* デスクトップ用ユーザー情報 */}
            <div className="hidden sm:block text-right mr-2">
              <div className="text-sm font-medium text-gray-900 truncate max-w-40 lg:max-w-none">
                {user.full_name || user.username}
              </div>
              {isAdmin && (
                <div className="text-xs text-gray-500 truncate">
                  {user.role} • {user.admin_id || user.user_id}
                </div>
              )}
            </div>
            
            {/* モバイル用ユーザーアイコン */}
            <div className="block sm:hidden">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gray-200">
                <svg className="h-5 w-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
            </div>
            
            {/* ログアウトボタン */}
            <Button
              variant="outline"
              size="sm"
              onClick={logout}
              className="flex items-center"
            >
              <svg className="mr-1 h-4 w-4 sm:mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
              <span className="hidden sm:inline">ログアウト</span>
            </Button>
          </div>
          
        </div>
      </div>
    </header>
  );
};