import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Layout } from '@/components/layout/Layout';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

interface User {
  user_id: string;
  name?: string;
  full_name?: string;
  email?: string;
  created_at: string;
}

interface BulkCreateResult {
  created_users: Array<{
    name: string;
    email: string;
    user_id: string;
    password: string;
  }>;
  errors: Array<{
    row: number;
    error: string;
  }>;
}

export const UserManagement: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [bulkCreateResult, setBulkCreateResult] = useState<BulkCreateResult | null>(null);
  const [showBulkResult, setShowBulkResult] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [isDeleting, setIsDeleting] = useState<string | null>(null);
  const [isChangingPassword, setIsChangingPassword] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    setIsLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:8000/admin/users', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      if (!response.ok) throw new Error('ユーザー一覧取得に失敗しました');
      
      const data = await response.json();
      console.log('API Response:', data); // デバッグ用
      const usersArray = data.users || [];
      console.log('Users Array:', usersArray); // デバッグ用
      
      // データの正規化
      const normalizedUsers = usersArray.map((user: any) => ({
        ...user,
        name: user.name || user.full_name || user.username,
        email: user.email || '',
        user_id: user.user_id || '',
        created_at: user.created_at || new Date().toISOString()
      }));
      
      setUsers(normalizedUsers);
    } catch (error) {
      console.error('Failed to load users:', error);
      alert('ユーザー一覧の読み込みに失敗しました');
    } finally {
      setIsLoading(false);
    }
  };

  const uploadUsersCsv = async () => {
    if (!csvFile) return;

    setIsLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', csvFile);

      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:8000/admin/users/bulk-create', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      if (!response.ok) throw new Error('CSV処理に失敗しました');

      const result = await response.json();
      setBulkCreateResult(result);
      setShowBulkResult(true);
      setCsvFile(null);
      
      // ユーザー一覧を再読み込み
      await loadUsers();
    } catch (error) {
      console.error('Failed to upload users CSV:', error);
      alert('CSVアップロードに失敗しました');
    } finally {
      setIsLoading(false);
    }
  };

  const deleteUser = async (userId: string, userName: string) => {
    if (!confirm(`ユーザー「${userName}」を削除しますか？`)) return;
    
    setIsDeleting(userId);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`http://localhost:8000/admin/users/${userId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) throw new Error('削除に失敗しました');
      
      alert('ユーザーを削除しました');
      await loadUsers();
    } catch (error) {
      console.error('Failed to delete user:', error);
      alert('ユーザー削除に失敗しました');
    } finally {
      setIsDeleting(null);
    }
  };

  const resetPassword = async (userId: string, userName: string) => {
    if (!confirm(`ユーザー「${userName}」のパスワードをリセットしますか？`)) return;
    
    setIsChangingPassword(userId);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`http://localhost:8000/admin/users/${userId}/reset-password`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) throw new Error('パスワードリセットに失敗しました');
      
      const data = await response.json();
      alert(`新しいパスワード: ${data.new_password}`);
    } catch (error) {
      console.error('Failed to reset password:', error);
      alert('パスワードリセットに失敗しました');
    } finally {
      setIsChangingPassword(null);
    }
  };

  const viewUserDetail = (userId: string) => {
    navigate(`/admin/users/${userId}`);
  };

  const exportBulkResultCsv = () => {
    if (!bulkCreateResult) return;
    
    const csvContent = [
      '氏名,メールアドレス,User ID,ログインパスワード',
      ...bulkCreateResult.created_users.map(user => 
        `${user.name},${user.email},${user.user_id},${user.password}`
      )
    ].join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'created_users.csv';
    link.click();
  };

  // フィルタリングされたユーザーリスト
  const filteredUsers = users.filter(user =>
    (user.name || user.full_name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
    (user.email || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
    (user.user_id || '').toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <Layout>
      <div className="space-y-8">
        {/* ヘッダー */}
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-lg p-8">
          <h1 className="text-3xl font-bold text-white mb-2">
            ユーザー管理
          </h1>
          <p className="text-blue-100">
            ユーザーの一括作成、一覧表示、詳細管理
          </p>
        </div>

        {/* 上段: ユーザー一括作成機能 */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-gray-900">ユーザー一括作成</h2>
            <div className="text-sm text-gray-500">
              CSV形式: 氏名, メールアドレス
            </div>
          </div>
          
          <div className="space-y-4">
            <div className="flex items-center gap-4">
              <Input
                type="file"
                accept=".csv"
                onChange={(e) => setCsvFile(e.target.files?.[0] || null)}
                className="flex-1"
              />
              <Button
                onClick={uploadUsersCsv}
                disabled={!csvFile || isLoading}
                className="min-w-[120px]"
              >
                {isLoading ? (
                  <LoadingSpinner size="sm" />
                ) : (
                  'CSVアップロード'
                )}
              </Button>
            </div>
            
            {/* 説明テキスト */}
            <div className="text-sm text-gray-600 bg-gray-50 p-3 rounded-lg">
              <p className="font-medium">CSV形式について:</p>
              <ul className="mt-1 ml-4 list-disc">
                <li>1列目: 氏名（必須）</li>
                <li>2列目: メールアドレス（必須）</li>
                <li>ヘッダー行は不要です</li>
                <li>user IDとパスワードは自動生成されます</li>
              </ul>
            </div>
          </div>
        </Card>

        {/* 一括作成結果表示 */}
        {showBulkResult && bulkCreateResult && (
          <Card className="p-6 border-green-200">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-green-800">
                一括作成結果
              </h3>
              <Button
                onClick={() => setShowBulkResult(false)}
                variant="outline"
                size="sm"
              >
                閉じる
              </Button>
            </div>
            
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center p-4 bg-green-50 rounded-lg">
                  <div className="text-2xl font-bold text-green-600">
                    {bulkCreateResult.created_users.length}
                  </div>
                  <div className="text-sm text-green-600">作成成功</div>
                </div>
                <div className="text-center p-4 bg-red-50 rounded-lg">
                  <div className="text-2xl font-bold text-red-600">
                    {bulkCreateResult.errors.length}
                  </div>
                  <div className="text-sm text-red-600">エラー</div>
                </div>
              </div>
              
              {bulkCreateResult.created_users.length > 0 && (
                <div>
                  <div className="flex justify-between items-center mb-3">
                    <h4 className="font-medium">作成されたユーザー</h4>
                    <Button
                      onClick={exportBulkResultCsv}
                      size="sm"
                      variant="outline"
                    >
                      CSV出力
                    </Button>
                  </div>
                  <div className="bg-gray-50 p-3 rounded text-sm max-h-40 overflow-y-auto">
                    {bulkCreateResult.created_users.map((user, index) => (
                      <div key={index} className="mb-1">
                        {user.name} ({user.email}) → ID: {user.user_id}, PW: {user.password}
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {bulkCreateResult.errors.length > 0 && (
                <div>
                  <h4 className="font-medium text-red-600 mb-3">エラー詳細</h4>
                  <div className="bg-red-50 p-3 rounded text-sm max-h-40 overflow-y-auto">
                    {bulkCreateResult.errors.map((error, index) => (
                      <div key={index} className="mb-1 text-red-700">
                        行{error.row}: {error.error}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </Card>
        )}

        {/* 下段: ユーザー一覧 */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-gray-900">ユーザー一覧</h2>
            <div className="flex items-center gap-4">
              <Input
                type="text"
                placeholder="名前、メール、IDで検索..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-64"
              />
              <div className="text-sm text-gray-500">
                {filteredUsers.length} / {users.length} 件
              </div>
            </div>
          </div>
          
          {isLoading ? (
            <div className="text-center py-8">
              <LoadingSpinner size="lg" text="読み込み中..." />
            </div>
          ) : filteredUsers.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              {searchTerm ? '該当するユーザーが見つかりません' : 'ユーザーがありません'}
            </div>
          ) : (
            <div className="space-y-3">
              {filteredUsers.map((user) => (
                <div key={user.user_id} className="border rounded-lg p-4 hover:bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-900">
                        {user.name || user.full_name || user.user_id}
                      </h3>
                      <p className="text-sm text-gray-600">
                        {user.email || '（メールアドレス未設定）'}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        ID: {user.user_id} • 作成: {new Date(user.created_at).toLocaleDateString('ja-JP')}
                      </p>
                    </div>
                    
                    <div className="flex items-center gap-2 ml-4">
                      <Button
                        onClick={() => viewUserDetail(user.user_id)}
                        size="sm"
                        variant="outline"
                        className="min-w-[60px]"
                      >
                        詳細
                      </Button>
                      
                      <Button
                        onClick={() => resetPassword(user.user_id, user.name || user.full_name || user.user_id)}
                        size="sm"
                        variant="outline"
                        disabled={isChangingPassword === user.user_id}
                        className="min-w-[80px]"
                      >
                        {isChangingPassword === user.user_id ? (
                          <LoadingSpinner size="xs" />
                        ) : (
                          'PW変更'
                        )}
                      </Button>
                      
                      <Button
                        onClick={() => deleteUser(user.user_id, user.name || user.full_name || user.user_id)}
                        size="sm"
                        variant="danger"
                        disabled={isDeleting === user.user_id}
                        className="min-w-[60px]"
                      >
                        {isDeleting === user.user_id ? (
                          <LoadingSpinner size="xs" />
                        ) : (
                          '削除'
                        )}
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </Layout>
  );
};