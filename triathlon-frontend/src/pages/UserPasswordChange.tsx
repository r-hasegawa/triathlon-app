import React, { useState, useEffect } from 'react';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface PasswordChangeData {
  currentPassword: string;
  newUsername: string;
  newPassword: string;
  confirmPassword: string;
}

interface ValidationErrors {
  currentPassword?: string;
  newUsername?: string;
  newPassword?: string;
  confirmPassword?: string;
}

interface UserInfo {
  username: string;
  user_id: string;
  full_name?: string;
}

const UserPasswordChange: React.FC = () => {
  const [currentUser, setCurrentUser] = useState<UserInfo | null>(null);
  const [formData, setFormData] = useState<PasswordChangeData>({
    currentPassword: '',
    newUsername: '',
    newPassword: '',
    confirmPassword: '',
  });

  const [showPasswords, setShowPasswords] = useState({
    current: false,
    new: false,
    confirm: false,
  });

  const [errors, setErrors] = useState<ValidationErrors>({});
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingUser, setIsLoadingUser] = useState(true);
  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  // 現在のユーザー情報を取得
  useEffect(() => {
    const fetchCurrentUser = async () => {
      try {
        const token = localStorage.getItem('access_token');
        if (!token) {
          window.location.href = '/login';
          return;
        }

        const response = await fetch(`${API_BASE_URL}/auth/me`, {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });

        if (!response.ok) {
          throw new Error('ユーザー情報の取得に失敗しました');
        }

        const userData = await response.json();
        setCurrentUser(userData);
        // 新しいユーザー名のデフォルト値を現在のユーザー名に設定
        setFormData(prev => ({ ...prev, newUsername: userData.username }));
      } catch (error) {
        console.error('Failed to fetch user info:', error);
        setErrorMessage('ユーザー情報の取得に失敗しました。再度ログインしてください。');
        setTimeout(() => {
          window.location.href = '/login';
        }, 2000);
      } finally {
        setIsLoadingUser(false);
      }
    };

    fetchCurrentUser();
  }, []);

  // フォーム入力ハンドラー
  const handleInputChange = (field: keyof PasswordChangeData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // エラーメッセージをクリア
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: undefined }));
    }
    setErrorMessage('');
    setSuccessMessage('');
  };

  // バリデーション
  const validateForm = (): boolean => {
    const newErrors: ValidationErrors = {};

    if (!formData.currentPassword) {
      newErrors.currentPassword = '現在のパスワードを入力してください';
    }

    if (!formData.newUsername.trim()) {
      newErrors.newUsername = '新しいユーザー名を入力してください';
    } else if (formData.newUsername.length < 3) {
      newErrors.newUsername = 'ユーザー名は3文字以上で入力してください';
    }

    if (!formData.newPassword) {
      newErrors.newPassword = '新しいパスワードを入力してください';
    } else if (formData.newPassword.length < 6) {
      newErrors.newPassword = 'パスワードは6文字以上で入力してください';
    }

    if (!formData.confirmPassword) {
      newErrors.confirmPassword = 'パスワード確認を入力してください';
    } else if (formData.newPassword !== formData.confirmPassword) {
      newErrors.confirmPassword = 'パスワードが一致しません';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // パスワード変更処理
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm() || !currentUser) {
      return;
    }

    setIsLoading(true);
    setErrorMessage('');
    setSuccessMessage('');

    try {
      // 1. 現在の認証情報でログイン確認
      const loginFormData = new FormData();
      loginFormData.append('username', currentUser.username);
      loginFormData.append('password', formData.currentPassword);

      const loginResponse = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        body: loginFormData,
      });

      if (!loginResponse.ok) {
        throw new Error('現在のパスワードが正しくありません');
      }

      const loginData = await loginResponse.json();
      const token = loginData.access_token;

      if (loginData.user_info.is_admin) {
        throw new Error('管理者アカウントはこのページでは変更できません。管理者用ページをご利用ください。');
      }

      // 2. パスワード変更APIを呼び出し
      const changeResponse = await fetch(`${API_BASE_URL}/auth/user/change-credentials`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          new_username: formData.newUsername,
          new_password: formData.newPassword,
        }),
      });

      if (!changeResponse.ok) {
        const errorData = await changeResponse.json();
        throw new Error(errorData.detail || 'パスワード変更に失敗しました');
      }

      // 成功時の処理
      setSuccessMessage('ユーザー名とパスワードが正常に変更されました。新しい認証情報でログインしてください。');
      
      // フォームをリセット
      setFormData({
        currentPassword: '',
        newUsername: '',
        newPassword: '',
        confirmPassword: '',
      });

      // ローカルストレージをクリア
      localStorage.removeItem('access_token');
      localStorage.removeItem('user_info');

      // 5秒後にログインページにリダイレクト
      setTimeout(() => {
        window.location.href = '/login';
      }, 5000);

    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : '予期しないエラーが発生しました');
    } finally {
      setIsLoading(false);
    }
  };

  const togglePasswordVisibility = (field: 'current' | 'new' | 'confirm') => {
    setShowPasswords(prev => ({ ...prev, [field]: !prev[field] }));
  };

  if (isLoadingUser) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-green-50 flex items-center justify-center">
        <div className="text-center">
          <svg className="animate-spin h-12 w-12 text-green-600 mx-auto mb-4" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <p className="text-gray-600">ユーザー情報を読み込み中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-green-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="bg-white shadow-2xl rounded-2xl overflow-hidden">
          {/* ヘッダー */}
          <div className="bg-gradient-to-r from-green-600 to-green-700 px-8 py-6">
            <div className="flex items-center gap-3">
              <div className="bg-white bg-opacity-20 p-3 rounded-lg">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">認証情報変更</h1>
                <p className="text-green-100 text-sm mt-1">User Credentials Change</p>
              </div>
            </div>
          </div>

          {/* フォーム */}
          <form onSubmit={handleSubmit} className="p-8 space-y-6">
            {/* 成功メッセージ */}
            {successMessage && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-start gap-3">
                <svg className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div className="text-green-800 text-sm">{successMessage}</div>
              </div>
            )}

            {/* エラーメッセージ */}
            {errorMessage && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
                <svg className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div className="text-red-800 text-sm">{errorMessage}</div>
              </div>
            )}

            {/* 現在の認証情報 */}
            <div className="space-y-4">
              <h2 className="text-lg font-semibold text-gray-900 border-b pb-2">現在の認証情報</h2>
              
              {/* 現在のユーザー名（表示のみ） */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  現在のユーザー名
                </label>
                <div className="w-full px-4 py-2.5 border border-gray-300 rounded-lg bg-gray-50 text-gray-700">
                  {currentUser?.username || '読み込み中...'}
                </div>
                <p className="mt-1 text-xs text-gray-500">※ 現在ログイン中のアカウント</p>
              </div>

              {/* 現在のパスワード */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  現在のパスワード <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <input
                    type={showPasswords.current ? 'text' : 'password'}
                    value={formData.currentPassword}
                    onChange={(e) => handleInputChange('currentPassword', e.target.value)}
                    className={`w-full px-4 py-2.5 pr-12 border rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition ${
                      errors.currentPassword ? 'border-red-300 bg-red-50' : 'border-gray-300'
                    }`}
                    placeholder="••••••••"
                    autoComplete="current-password"
                  />
                  <button
                    type="button"
                    onClick={() => togglePasswordVisibility('current')}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                  >
                    {showPasswords.current ? (
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                      </svg>
                    ) : (
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                      </svg>
                    )}
                  </button>
                </div>
                {errors.currentPassword && (
                  <p className="mt-1 text-sm text-red-600">{errors.currentPassword}</p>
                )}
              </div>
            </div>

            {/* 新しい認証情報 */}
            <div className="space-y-4">
              <h2 className="text-lg font-semibold text-gray-900 border-b pb-2">新しい認証情報</h2>
              
              {/* 新しいユーザー名 */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  新しいユーザー名 <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.newUsername}
                  onChange={(e) => handleInputChange('newUsername', e.target.value)}
                  className={`w-full px-4 py-2.5 border rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition ${
                    errors.newUsername ? 'border-red-300 bg-red-50' : 'border-gray-300'
                  }`}
                  placeholder="新しいユーザー名（3文字以上）"
                  autoComplete="new-username"
                />
                {errors.newUsername && (
                  <p className="mt-1 text-sm text-red-600">{errors.newUsername}</p>
                )}
              </div>

              {/* 新しいパスワード */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  新しいパスワード <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <input
                    type={showPasswords.new ? 'text' : 'password'}
                    value={formData.newPassword}
                    onChange={(e) => handleInputChange('newPassword', e.target.value)}
                    className={`w-full px-4 py-2.5 pr-12 border rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition ${
                      errors.newPassword ? 'border-red-300 bg-red-50' : 'border-gray-300'
                    }`}
                    placeholder="新しいパスワード（6文字以上）"
                    autoComplete="new-password"
                  />
                  <button
                    type="button"
                    onClick={() => togglePasswordVisibility('new')}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                  >
                    {showPasswords.new ? (
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                      </svg>
                    ) : (
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                      </svg>
                    )}
                  </button>
                </div>
                {errors.newPassword && (
                  <p className="mt-1 text-sm text-red-600">{errors.newPassword}</p>
                )}
              </div>

              {/* パスワード確認 */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  パスワード確認 <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <input
                    type={showPasswords.confirm ? 'text' : 'password'}
                    value={formData.confirmPassword}
                    onChange={(e) => handleInputChange('confirmPassword', e.target.value)}
                    className={`w-full px-4 py-2.5 pr-12 border rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition ${
                      errors.confirmPassword ? 'border-red-300 bg-red-50' : 'border-gray-300'
                    }`}
                    placeholder="パスワードを再入力"
                    autoComplete="new-password"
                  />
                  <button
                    type="button"
                    onClick={() => togglePasswordVisibility('confirm')}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                  >
                    {showPasswords.confirm ? (
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                      </svg>
                    ) : (
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                      </svg>
                    )}
                  </button>
                </div>
                {errors.confirmPassword && (
                  <p className="mt-1 text-sm text-red-600">{errors.confirmPassword}</p>
                )}
              </div>
            </div>

            {/* 注意事項 */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="text-sm font-semibold text-blue-800 mb-2">📌 注意事項</h3>
              <ul className="text-sm text-blue-700 space-y-1 list-disc list-inside">
                <li>変更後は新しいユーザー名とパスワードでログインしてください</li>
                <li>変更した認証情報は安全に保管してください</li>
                <li>変更後、現在のセッションは無効になります</li>
              </ul>
            </div>

            {/* 送信ボタン */}
            <button
              type="submit"
              disabled={isLoading}
              style={{
                background: isLoading 
                  ? 'linear-gradient(to right, #16a34a, #15803d)' 
                  : 'linear-gradient(to right, #16a34a, #15803d)'
              }}
              className="w-full text-white py-3 px-4 rounded-lg font-semibold hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition shadow-lg"
            >
              {isLoading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  処理中...
                </span>
              ) : (
                '認証情報を変更する'
              )}
            </button>
          </form>
        </div>

        {/* フッター */}
        <div className="text-center mt-6 text-sm text-gray-600">
          <p>© 2025 Triathlon Sensor Data Feedback System</p>
        </div>
      </div>
    </div>
  );
};

export default UserPasswordChange;