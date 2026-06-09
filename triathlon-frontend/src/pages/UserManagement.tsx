import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Layout } from '@/components/layout/Layout';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
// アイコンは使用しない、またはプロジェクトで既に使っているアイコンライブラリに置き換えてください

interface User {
  user_id: string;
  name?: string;
  full_name?: string;
  username?: string;
  email?: string;
  created_at: string;
  sensor_breakdown?: {
    skin_temperature: number;
    core_temperature: number;
    heart_rate: number;
  };
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

interface ImportError {
  row: number;
  user_id: string;
  username: string;
  error: string;
}

interface ImportedUser {
  user_id: string;
  username: string;
  full_name: string;
  email: string;
}

interface ImportResult {
  success: boolean;
  total_records: number;
  imported_count: number;
  skipped_count: number;
  error_count: number;
  errors: ImportError[];
  imported_users: ImportedUser[];
}

export const UserManagement: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [bulkCreateResult, setBulkCreateResult] = useState<BulkCreateResult | null>(null);
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const [showBulkResult, setShowBulkResult] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [isDeleting, setIsDeleting] = useState<string | null>(null);
  const [isChangingPassword, setIsChangingPassword] = useState<string | null>(null);
  const [importing, setImporting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // ページネーション用のstate
  const [currentPage, setCurrentPage] = useState(1);
  const [totalUsers, setTotalUsers] = useState(0);
  const usersPerPage = 50;
  
  const navigate = useNavigate();

  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  // 20260609 変更後
  useEffect(() => {
    const timer = setTimeout(() => {
      loadUsers(1);
    }, searchTerm ? 400 : 0);
    return () => clearTimeout(timer);
  }, [searchTerm]);

  const loadUsers = async (page: number = 1) => {
    setIsLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const skip = (page - 1) * usersPerPage;
      const params = new URLSearchParams({
        skip: String(skip),
        limit: String(usersPerPage),
      });
      if (searchTerm.trim()) {
        params.append('search', searchTerm.trim());
      }
      const response = await fetch(
        `${API_BASE_URL}/admin/users?${params}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );
      
      if (!response.ok) throw new Error('ユーザー一覧取得に失敗しました');
      
      const data = await response.json();
      const usersArray = data.users || [];
      const pagination = data.pagination || {};
      
      const normalizedUsers = usersArray.map((user: any) => ({
        ...user,
        name: user.name || user.full_name || user.username,
        email: user.email || '',
        user_id: user.user_id || '',
        created_at: user.created_at || new Date().toISOString()
      }));
      
      setUsers(normalizedUsers);
      setTotalUsers(pagination.total || 0);
      setCurrentPage(page);
    } catch (error) {
      console.error('Failed to load users:', error);
      alert('ユーザー一覧の読み込みに失敗しました');
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setCsvFile(e.target.files[0]);
      setImportResult(null);
      setError(null);
      setBulkCreateResult(null);
      setShowBulkResult(false);
    }
  };

  const handleImport = async () => {
    if (!csvFile) {
      setError('CSVファイルを選択してください');
      return;
    }

    setImporting(true);
    setError(null);
    setImportResult(null);

    const formData = new FormData();
    formData.append('file', csvFile);

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_BASE_URL}/admin/import-users`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'インポート中にエラーが発生しました');
      }

      const result = await response.json();
      setImportResult(result);
      
      // ファイル選択をクリア（連続してインポートできるように）
      setCsvFile(null);
      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
      if (fileInput) fileInput.value = '';
      
      // ユーザー一覧を再読み込み
      await loadUsers();
    } catch (err: any) {
      setError(err.message || 'インポート中にエラーが発生しました');
    } finally {
      setImporting(false);
    }
  };

  const downloadTemplate = () => {
    const csvContent = 'ID,user_name,full_name,e-mail,password\nuser001,tanaka,田中太郎,tanaka@example.com,password123\nuser002,sato,佐藤花子,sato@example.com,password456';
    // UTF-8 BOM を追加してExcelでの文字化けを防ぐ
    const bom = new Uint8Array([0xEF, 0xBB, 0xBF]);
    const blob = new Blob([bom, csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'user_import_template.csv';
    link.click();
  };

  const deleteUser = async (userId: string, userName: string) => {
    if (!confirm(`ユーザー「${userName}」を削除しますか？`)) return;
    
    setIsDeleting(userId);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_BASE_URL}/admin/users/${userId}`, {
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
      const response = await fetch(`${API_BASE_URL}/admin/users/${userId}/reset-password`, {
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

  const totalPages = Math.ceil(totalUsers / usersPerPage);
  const startIndex = (currentPage - 1) * usersPerPage + 1;
  const endIndex = Math.min(currentPage * usersPerPage, totalUsers);

  const handlePageChange = (newPage: number) => {
    if (newPage >= 1 && newPage <= totalPages) {
      loadUsers(newPage);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  return (
    <Layout>
      <div className="max-w-7xl mx-auto p-6 space-y-6">
        <h1 className="text-3xl font-bold text-gray-900">ユーザー管理</h1>

        {/* ユーザー一括登録セクション */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">ユーザー一括登録</h2>

          {/* テンプレートダウンロード */}
          <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <h3 className="font-semibold mb-2">📋 CSVフォーマット</h3>
            <p className="text-sm text-gray-600 mb-3">
              以下の形式でCSVファイルを作成してください：
            </p>
            <div className="bg-white p-3 rounded border font-mono text-xs mb-3">
              ID,user_name,full_name,e-mail,password<br />
              user001,tanaka,田中太郎,tanaka@example.com,password123
            </div>
            <button
              onClick={downloadTemplate}
              className="flex items-center gap-2 px-4 py-2 rounded transition-colors"
              style={{ backgroundColor: '#2563eb', color: '#ffffff' }}
              onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#1d4ed8'}
              onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#2563eb'}
            >
              📥 テンプレートをダウンロード
            </button>
          </div>

          {/* ファイル選択 */}
          <div className="mb-6">
            <label className="block mb-2 font-semibold">CSVファイルを選択</label>
            <div className="flex items-center gap-4">
              <input
                type="file"
                accept=".csv"
                onChange={handleFileChange}
                className="flex-1 px-4 py-2 border rounded"
                disabled={importing}
              />
              <Button
                onClick={handleImport}
                disabled={!csvFile || importing}
                className={`flex items-center gap-2 ${
                  !csvFile || importing
                    ? 'bg-gray-300 cursor-not-allowed'
                    : 'bg-green-600 hover:bg-green-700'
                }`}
              >
                📤 {importing ? 'インポート中...' : 'インポート'}
              </Button>
            </div>
            {csvFile && (
              <p className="mt-2 text-sm text-gray-600">
                選択中: {csvFile.name}
              </p>
            )}
          </div>

          {/* エラー表示 */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
              <span className="text-red-600 text-xl flex-shrink-0">⚠️</span>
              <div className="flex-1">
                <p className="font-semibold text-red-800">エラー</p>
                <p className="text-red-700">{error}</p>
              </div>
            </div>
          )}

          {/* インポート結果表示 */}
          {importResult && (
            <div className="space-y-4">
              <div className={`p-4 rounded-lg border ${
                importResult.success ? 'bg-green-50 border-green-200' : 'bg-yellow-50 border-yellow-200'
              }`}>
                <div className="flex items-start gap-3">
                  <span className={`text-2xl ${importResult.success ? 'text-green-600' : 'text-yellow-600'}`}>
                    {importResult.success ? '✓' : '⚠'}
                  </span>
                  <div className="flex-1">
                    <h3 className="font-semibold mb-2">インポート結果</h3>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="font-semibold">総レコード数:</span> {importResult.total_records}
                      </div>
                      <div>
                        <span className="font-semibold text-green-600">インポート成功:</span> {importResult.imported_count}
                      </div>
                      <div>
                        <span className="font-semibold text-yellow-600">スキップ:</span> {importResult.skipped_count}
                      </div>
                      <div>
                        <span className="font-semibold text-red-600">エラー:</span> {importResult.error_count}
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* エラー詳細 */}
              {importResult.errors.length > 0 && (
                <div className="border rounded-lg overflow-hidden">
                  <div className="bg-red-100 px-4 py-2 font-semibold text-red-800">
                    エラー詳細 ({importResult.errors.length}件)
                  </div>
                  <div className="max-h-64 overflow-y-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-gray-50 sticky top-0">
                        <tr>
                          <th className="px-4 py-2 text-left">行</th>
                          <th className="px-4 py-2 text-left">User ID</th>
                          <th className="px-4 py-2 text-left">Username</th>
                          <th className="px-4 py-2 text-left">エラー内容</th>
                        </tr>
                      </thead>
                      <tbody>
                        {importResult.errors.map((err, idx) => (
                          <tr key={idx} className="border-t hover:bg-gray-50">
                            <td className="px-4 py-2">{err.row}</td>
                            <td className="px-4 py-2">{err.user_id}</td>
                            <td className="px-4 py-2">{err.username}</td>
                            <td className="px-4 py-2 text-red-600">{err.error}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* インポート成功ユーザー */}
              {importResult.imported_users.length > 0 && (
                <div className="border rounded-lg overflow-hidden">
                  <div className="bg-green-100 px-4 py-2 font-semibold text-green-800">
                    インポート成功 ({importResult.imported_users.length}件)
                  </div>
                  <div className="max-h-64 overflow-y-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-gray-50 sticky top-0">
                        <tr>
                          <th className="px-4 py-2 text-left">User ID</th>
                          <th className="px-4 py-2 text-left">Username</th>
                          <th className="px-4 py-2 text-left">氏名</th>
                          <th className="px-4 py-2 text-left">Email</th>
                        </tr>
                      </thead>
                      <tbody>
                        {importResult.imported_users.map((user, idx) => (
                          <tr key={idx} className="border-t hover:bg-gray-50">
                            <td className="px-4 py-2">{user.user_id}</td>
                            <td className="px-4 py-2">{user.username}</td>
                            <td className="px-4 py-2">{user.full_name}</td>
                            <td className="px-4 py-2">{user.email}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}
        </Card>

        {/* ユーザー一覧セクション */}
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
                {startIndex}-{endIndex} / {totalUsers} 件
              </div>
            </div>
          </div>
          
          {isLoading ? (
            <div className="text-center py-8">
              <LoadingSpinner size="lg" text="読み込み中..." />
            </div>
          ) : users.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              {searchTerm ? '該当するユーザーが見つかりません' : 'ユーザーがありません'}
            </div>
          ) : (
            <div className="space-y-3">
              {users.map((user) => (
                <div key={user.user_id} className="border rounded-lg p-4 hover:bg-gray-50">
                  <div className="flex items-center justify-between">
                    {/* --- 20260609 ユーザ表示変更 --- */}
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
                      {/* センサーデータ件数バッジ */}
                      <div style={{ display: 'flex', gap: '6px', marginTop: '6px', flexWrap: 'wrap' }}>
                        {(
                          [
                            { label: '体表温', key: 'skin_temperature' },
                            { label: '深部温', key: 'core_temperature' },
                            { label: '心拍',   key: 'heart_rate' },
                          ] as const
                        ).map(({ label, key }) => {
                          const count = user.sensor_breakdown?.[key] ?? 0;
                          const hasData = count > 0;
                          return (
                            <span
                              key={key}
                              style={{
                                display: 'inline-block',
                                padding: '1px 8px',
                                borderRadius: '9999px',
                                fontSize: '11px',
                                fontWeight: 600,
                                backgroundColor: hasData ? '#dcfce7' : '#fee2e2',
                                color: hasData ? '#166534' : '#991b1b',
                                border: `1px solid ${hasData ? '#bbf7d0' : '#fecaca'}`,
                              }}
                            >
                              {label} {count.toLocaleString()}
                            </span>
                          );
                        })}
                      </div>
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

          {/* ページネーション */}
          {!isLoading && totalUsers > usersPerPage && (
            <div className="mt-6 flex items-center justify-between border-t pt-4">
              <div className="text-sm text-gray-700">
                ページ {currentPage} / {totalPages} （全 {totalUsers} 件）
              </div>
              
              <div className="flex items-center gap-2">
                <Button
                  onClick={() => handlePageChange(1)}
                  disabled={currentPage === 1}
                  size="sm"
                  variant="outline"
                  className="min-w-[70px]"
                >
                  最初
                </Button>
                
                <Button
                  onClick={() => handlePageChange(currentPage - 1)}
                  disabled={currentPage === 1}
                  size="sm"
                  variant="outline"
                  className="min-w-[70px]"
                >
                  前へ
                </Button>
                
                {/* ページ番号ボタン */}
                <div className="flex items-center gap-1">
                  {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                    let pageNum;
                    if (totalPages <= 5) {
                      pageNum = i + 1;
                    } else if (currentPage <= 3) {
                      pageNum = i + 1;
                    } else if (currentPage >= totalPages - 2) {
                      pageNum = totalPages - 4 + i;
                    } else {
                      pageNum = currentPage - 2 + i;
                    }
                    
                    return (
                      <button
                        key={pageNum}
                        onClick={() => handlePageChange(pageNum)}
                        className={`min-w-[40px] h-9 px-3 rounded ${
                          currentPage === pageNum
                            ? 'bg-blue-600 text-white font-semibold'
                            : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                        }`}
                      >
                        {pageNum}
                      </button>
                    );
                  })}
                </div>
                
                <Button
                  onClick={() => handlePageChange(currentPage + 1)}
                  disabled={currentPage === totalPages}
                  size="sm"
                  variant="outline"
                  className="min-w-[70px]"
                >
                  次へ
                </Button>
                
                <Button
                  onClick={() => handlePageChange(totalPages)}
                  disabled={currentPage === totalPages}
                  size="sm"
                  variant="outline"
                  className="min-w-[70px]"
                >
                  最後
                </Button>
              </div>
            </div>
          )}
        </Card>
      </div>
    </Layout>
  );
};