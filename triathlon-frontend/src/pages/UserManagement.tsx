import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Layout } from '@/components/layout/Layout';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { UserTable, UserInfo } from '@/components/admin/UserTable';
import { UserModal, UserFormData } from '@/components/admin/UserModal';
import { UserFiltersComponent, UserFilters } from '@/components/admin/UserFilters';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { adminService } from '@/services/adminService';

export const UserManagement: React.FC = () => {
  const navigate = useNavigate();  // useNavigate フックを使用
  const [users, setUsers] = useState<UserInfo[]>([]);
  const [filteredUsers, setFilteredUsers] = useState<UserInfo[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [showUserModal, setShowUserModal] = useState(false);
  const [editingUser, setEditingUser] = useState<UserInfo | null>(null);
  const [filters, setFilters] = useState({
    search: '',
    status: 'all' as 'all' | 'active' | 'inactive',
    hasData: 'all' as 'all' | 'with-data' | 'without-data'
  });
  const [isModalLoading, setIsModalLoading] = useState(false);

  useEffect(() => {
    fetchUsers();
  }, []);

  useEffect(() => {
    let filtered = [...users];

    // 検索フィルター
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      filtered = filtered.filter(user =>
        user.username.toLowerCase().includes(searchLower) ||
        user.full_name.toLowerCase().includes(searchLower) ||
        user.user_id.toLowerCase().includes(searchLower) ||
        (user.email && user.email.toLowerCase().includes(searchLower))
      );
    }

    // ステータスフィルター
    if (filters.status !== 'all') {
      filtered = filtered.filter(user =>
        filters.status === 'active' ? user.is_active : !user.is_active
      );
    }

    // データ有無フィルター
    if (filters.hasData !== 'all') {
      filtered = filtered.filter(user => {
        const hasData = (user.sensor_count || 0) > 0;
        return filters.hasData === 'with-data' ? hasData : !hasData;
      });
    }

    setFilteredUsers(filtered);
  }, [users, filters]);

  const fetchUsers = async () => {
    try {
      setIsLoading(true);
      setError('');
      const usersData = await adminService.getUsersWithStats();
      setUsers(usersData);
    } catch (err: any) {
      console.error('Error fetching users:', err);
      setError('ユーザー一覧の取得に失敗しました');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateUser = () => {
    setEditingUser(null);
    setShowUserModal(true);
  };

  const handleEditUser = (user: UserInfo) => {
    setEditingUser(user);
    setShowUserModal(true);
  };

  const handleDeleteUser = async (user: UserInfo) => {
    if (!confirm(`ユーザー「${user.username}」を削除しますか？\n\nこの操作は取り消せません。関連するセンサデータも削除されます。`)) {
      return;
    }

    try {
      await adminService.deleteUser(user.user_id);
      await fetchUsers();
      alert('ユーザーを削除しました');
    } catch (error: any) {
      console.error('Delete user error:', error);
      alert(`ユーザーの削除に失敗しました: ${error.message}`);
    }
  };

  const handleViewData = (user: UserInfo) => {
    // 管理者モードでデータ詳細画面に遷移（ユーザー指定）
    navigate(`/data-detail?user_id=${user.user_id}`);
    
    // 新しいタブで開きたい場合は以下を使用
    // window.open(`/data-detail?user_id=${user.user_id}`, '_blank');
  };

  const handleResetPassword = async (user: UserInfo) => {
    const newPassword = prompt(`ユーザー「${user.username}」の新しいパスワードを入力してください:`);
    
    if (!newPassword) {
      return;
    }

    if (newPassword.length < 6) {
      alert('パスワードは6文字以上で入力してください');
      return;
    }

    try {
      await adminService.resetUserPassword(user.user_id, newPassword);
      alert(`パスワードを変更しました。\n新しいパスワード: ${newPassword}`);
    } catch (error: any) {
      console.error('Reset password error:', error);
      alert(`パスワードのリセットに失敗しました: ${error.message}`);
    }
  };

  const handleSaveUser = async (userData: any) => {
    try {
      if (editingUser) {
        // 既存ユーザーの更新
        await adminService.updateUser(editingUser.user_id, userData);
        alert('ユーザー情報を更新しました');
      } else {
        // 新規ユーザーの作成
        await adminService.createUser(userData);
        alert('ユーザーを作成しました');
      }
      
      setShowUserModal(false);
      await fetchUsers();
    } catch (error: any) {
      console.error('Save user error:', error);
      alert(`ユーザーの保存に失敗しました: ${error.message}`);
    }
  };

  const handleFiltersReset = () => {
    setFilters({
      search: '',
      status: 'all',
      hasData: 'all',
    });
  };

  return (
    <Layout>
      <div className="space-y-6">
        {/* ヘッダー */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">ユーザー管理</h1>
            <p className="mt-1 text-sm text-gray-500">
              被験者アカウントの作成・編集・削除を行えます
            </p>
          </div>
          
          <div className="flex space-x-2">
            <Button
              variant="outline"
              onClick={fetchUsers}
              disabled={isLoading}
              size="sm"
            >
              🔄 更新
            </Button>
            
            <Button
              variant="primary"
              onClick={handleCreateUser}
              size="sm"
            >
              ➕ 新規ユーザー
            </Button>
          </div>
        </div>

        {/* エラー表示 */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex justify-between items-center">
              <p className="text-sm text-red-600">{error}</p>
              <Button
                onClick={fetchUsers}
                variant="outline"
                size="sm"
              >
                再試行
              </Button>
            </div>
          </div>
        )}

        {/* 統計カード */}
        {!isLoading && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <div className="text-center">
                <p className="text-2xl font-bold text-blue-600">
                  {users.length}
                </p>
                <p className="text-sm text-gray-500">総ユーザー数</p>
              </div>
            </Card>
            
            <Card>
              <div className="text-center">
                <p className="text-2xl font-bold text-green-600">
                  {users.filter(u => u.is_active).length}
                </p>
                <p className="text-sm text-gray-500">アクティブ</p>
              </div>
            </Card>
            
            <Card>
              <div className="text-center">
                <p className="text-2xl font-bold text-purple-600">
                  {users.filter(u => (u.sensor_count || 0) > 0).length}
                </p>
                <p className="text-sm text-gray-500">データあり</p>
              </div>
            </Card>
            
            <Card>
              <div className="text-center">
                <p className="text-2xl font-bold text-orange-600">
                  {users.reduce((sum, u) => sum + (u.sensor_count || 0), 0)}
                </p>
                <p className="text-sm text-gray-500">総センサー数</p>
              </div>
            </Card>
          </div>
        )}

        {/* フィルター */}
        <UserFiltersComponent
          filters={filters}
          onFiltersChange={setFilters}
          onReset={handleFiltersReset}
          userCount={filteredUsers.length}
        />

        {/* ユーザーテーブル */}
        <Card>
          {isLoading ? (
            <div className="flex justify-center items-center h-64">
              <LoadingSpinner size="lg" />
            </div>
          ) : (
            <UserTable
              users={filteredUsers}
              isLoading={isLoading}
              onEdit={handleEditUser}
              onDelete={handleDeleteUser}
              onViewData={handleViewData}
              onResetPassword={handleResetPassword}
            />
          )}
        </Card>

        {/* 使用方法のヒント */}
        {filteredUsers.length === 0 && !isLoading && !error && (
          <Card>
            <div className="text-center py-8 space-y-4">
              <div className="text-gray-400">
                <svg className="mx-auto h-16 w-16 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
                </svg>
              </div>
              
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  {filters.search || filters.status !== 'all' || filters.hasData !== 'all' 
                    ? 'フィルター条件に一致するユーザーが見つかりませんでした'
                    : 'ユーザーがまだ登録されていません'
                  }
                </h3>
                
                <div className="space-y-2">
                  {filters.search || filters.status !== 'all' || filters.hasData !== 'all' ? (
                    <p className="text-sm text-gray-600">
                      フィルター条件を変更するか、リセットしてください
                    </p>
                  ) : (
                    <p className="text-sm text-gray-600">
                      「新規ユーザー」ボタンから被験者を追加してください
                    </p>
                  )}
                </div>
                
                <div className="mt-4 flex justify-center space-x-2">
                  {(filters.search || filters.status !== 'all' || filters.hasData !== 'all') && (
                    <Button
                      variant="outline"
                      onClick={handleFiltersReset}
                      size="sm"
                    >
                      フィルターをリセット
                    </Button>
                  )}
                  
                  <Button
                    variant="primary"
                    onClick={handleCreateUser}
                    size="sm"
                  >
                    新規ユーザーを追加
                  </Button>
                </div>
              </div>
            </div>
          </Card>
        )}

        {/* ユーザーモーダル */}
        <UserModal
          isOpen={showUserModal}
          onClose={() => setShowUserModal(false)}
          onSave={handleSaveUser}
          editingUser={editingUser}
          isLoading={isModalLoading}
        />

        {/* 運用ガイド */}
        <Card title="ユーザー管理ガイド">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-medium text-gray-900 mb-2">📋 基本操作</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• <strong>編集</strong>: ユーザー情報の変更</li>
                <li>• <strong>データ</strong>: そのユーザーのセンサデータを表示</li>
                <li>• <strong>PW</strong>: パスワードをリセット</li>
                <li>• <strong>削除</strong>: ユーザーとデータを完全削除</li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-medium text-gray-900 mb-2">⚠️ 注意事項</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• ユーザー削除は取り消せません</li>
                <li>• 関連するセンサデータも同時削除されます</li>
                <li>• ユーザーIDは編集できません</li>
                <li>• パスワードは6文字以上で設定してください</li>
              </ul>
            </div>
          </div>
        </Card>
      </div>
    </Layout>
  );
};