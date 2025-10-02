import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card } from '@/components/ui/Card';

export const Login: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!username.trim() || !password.trim()) {
      setError('ユーザー名とパスワードを入力してください');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      await login(username.trim(), password);
      navigate('/dashboard');
    } catch (err: any) {
      console.error('Login error:', err);
      setError(
        err.response?.data?.detail || 
        'ログインに失敗しました。ユーザー名とパスワードを確認してください。'
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleTestLogin = (testUsername: string, testPassword: string) => {
    setUsername(testUsername);
    setPassword(testPassword);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-blue-50 flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8">
      {/* ヘッダーセクション */}
      <div className="mx-auto w-full max-w-md sm:max-w-md">
        <div className="text-center">
          {/* ロゴ */}
          <div 
            className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl shadow-lg"
            style={{
              background: 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)'
            }}
          >
            <svg className="h-8 w-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
                    
          <h1 className="mb-2 text-2xl font-bold text-gray-900 sm:text-3xl">
            トライアスロン
          </h1>
          <h2 className="mb-4 text-xl font-semibold text-primary-600 sm:text-2xl">
            センサデータシステム
          </h2>
          <p className="text-sm text-gray-600 sm:text-base">
            アカウントにサインインしてください
          </p>
        </div>
      </div>

      {/* ログインフォーム */}
      <div className="mx-auto mt-8 w-full max-w-md px-4 sm:px-0">
        <Card className="border-0 shadow-xl">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-4">
              <Input
                label="ユーザー名"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="ユーザー名を入力"
                autoComplete="username"
                disabled={isLoading}
                className="text-base sm:text-sm"
              />

              <Input
                label="パスワード"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="パスワードを入力"
                autoComplete="current-password"
                disabled={isLoading}
                className="text-base sm:text-sm"
              />
            </div>

            {error && (
              <div className="alert alert-error animate-slideIn">
                <div className="flex">
                  <svg className="h-5 w-5 flex-shrink-0 text-red-400 mr-2 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                  <p className="text-sm">{error}</p>
                </div>
              </div>
            )}

            <Button
              type="submit"
              className="w-full h-11 text-base font-semibold"
              isLoading={isLoading}
              disabled={isLoading}
            >
              {isLoading ? 'ログイン中...' : 'ログイン'}
            </Button>
          </form>

        </Card>

        {/* フッター情報 */}
        <div className="mt-8 text-center">
          <p className="text-xs text-gray-500">
            © 2025 トライアスロンセンサデータシステム
          </p>
        </div>
      </div>
    </div>
  );
};