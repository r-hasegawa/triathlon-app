import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/Button';

export const Header: React.FC = () => {
  const { user, logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();

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
              <div 
                className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary-600 mr-4 cursor-pointer"
                onClick={() => navigate(isAdmin ? '/admin/dashboard' : '/dashboard')}
              >
                <svg className="h-5 w-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              
              {/* レスポンシブタイトル */}
              <div className="flex flex-col mr-4">
                <h1 
                  className="hidden sm:block text-lg lg:text-xl font-bold text-gray-900 leading-tight cursor-pointer"
                  onClick={() => navigate(isAdmin ? '/admin/dashboard' : '/dashboard')}
                >
                  トライアスロンセンサデータシステム
                </h1>
                <h1 
                  className="block sm:hidden text-base font-bold text-gray-900 cursor-pointer"
                  onClick={() => navigate(isAdmin ? '/admin/dashboard' : '/dashboard')}
                >
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

      {/* 管理者専用ナビゲーション - 常に下部に表示 */}
      {isAdmin && (
        <div className="border-t border-gray-200 bg-gray-50">
          <div className="flex items-center gap-2 px-4 py-2 overflow-x-auto">
            <Button
              onClick={() => navigate('/admin/dashboard')}
              variant="outline"
              size="sm"
              className="flex items-center gap-1.5 text-gray-700 border-gray-300 bg-white hover:bg-gray-50 whitespace-nowrap"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
              </svg>
              TOP
            </Button>
            
            <Button
              onClick={() => navigate('/admin/users')}
              variant="outline"
              size="sm"
              className="flex items-center gap-1.5 text-blue-700 border-blue-200 bg-white hover:bg-blue-50 whitespace-nowrap"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
              ユーザ管理
            </Button>
            
            <Button
              onClick={() => navigate('/admin/competitions')}
              variant="outline"
              size="sm"
              className="flex items-center gap-1.5 text-green-700 border-green-200 bg-white hover:bg-green-50 whitespace-nowrap"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              大会管理
            </Button>
            
            <Button
              onClick={() => navigate('/admin/upload')}
              variant="outline"
              size="sm"
              className="flex items-center gap-1.5 text-purple-700 border-purple-200 bg-white hover:bg-purple-50 whitespace-nowrap"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              データ管理
            </Button>
          </div>
        </div>
      )}
    </header>
  );
};