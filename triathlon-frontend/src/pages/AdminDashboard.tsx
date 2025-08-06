import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Layout } from '@/components/layout/Layout';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { adminService, DashboardStats } from '@/services/adminService';

export const AdminDashboard: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchDashboardStats();
  }, []);

  const fetchDashboardStats = async () => {
    try {
      setIsLoading(true);
      setError('');
      const dashboardStats = await adminService.getDashboardStats();
      setStats(dashboardStats);
    } catch (err: any) {
      console.error('Error fetching dashboard stats:', err);
      setError('統計情報の取得に失敗しました');
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <Layout>
        <div className="flex justify-center items-center h-64">
          <LoadingSpinner size="lg" />
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-8">
        {/* ヘッダー */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">管理者ダッシュボード</h1>
            <p className="mt-1 text-sm text-gray-500">
              システム管理とデータ管理を行えます
            </p>
          </div>
          
          <Button onClick={fetchDashboardStats} variant="outline" size="sm">
            🔄 統計を更新
          </Button>
        </div>

        {/* エラー表示 */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex justify-between items-center">
              <p className="text-sm text-red-600">{error}</p>
              <Button
                onClick={fetchDashboardStats}
                variant="outline"
                size="sm"
              >
                再試行
              </Button>
            </div>
          </div>
        )}

        {/* システム統計 */}
        {stats && (
          <div>
            <h2 className="text-lg font-medium text-gray-900 mb-4">システム統計</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              {/* ユーザー統計 */}
              <Card>
                <div className="text-center">
                  <p className="text-3xl font-bold text-blue-600">{stats.total_users}</p>
                  <p className="text-sm text-gray-500 mb-2">総ユーザー数</p>
                  <div className="text-xs space-y-1">
                    <div className="flex justify-between">
                      <span className="text-green-600">アクティブ:</span>
                      <span className="font-medium">{stats.active_users}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">無効:</span>
                      <span className="font-medium">{stats.inactive_users}</span>
                    </div>
                  </div>
                </div>
              </Card>

              {/* データ統計 */}
              <Card>
                <div className="text-center">
                  <p className="text-3xl font-bold text-green-600">
                    {stats.total_data_records.toLocaleString()}
                  </p>
                  <p className="text-sm text-gray-500 mb-2">総データ数</p>
                  <div className="text-xs space-y-1">
                    <div className="flex justify-between">
                      <span className="text-green-600">直近7日:</span>
                      <span className="font-medium">{stats.recent_data_count.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">1ユーザー平均:</span>
                      <span className="font-medium">{stats.avg_records_per_user}</span>
                    </div>
                  </div>
                </div>
              </Card>

              {/* センサー統計 */}
              <Card>
                <div className="text-center">
                  <p className="text-3xl font-bold text-purple-600">{stats.total_sensors}</p>
                  <p className="text-sm text-gray-500 mb-2">登録センサー数</p>
                  <div className="text-xs space-y-1">
                    <div className="flex justify-between">
                      <span className="text-purple-600">1ユーザー平均:</span>
                      <span className="font-medium">{stats.avg_sensors_per_user}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">データあり:</span>
                      <span className="font-medium">{stats.users_with_data}名</span>
                    </div>
                  </div>
                </div>
              </Card>

              {/* 最近のアクティビティ */}
              <Card>
                <div className="text-center">
                  <p className="text-3xl font-bold text-orange-600">{stats.recent_uploads}</p>
                  <p className="text-sm text-gray-500 mb-2">直近アップロード数</p>
                  <div className="text-xs space-y-1">
                    <div className="flex justify-between">
                      <span className="text-orange-600">期間:</span>
                      <span className="font-medium">過去7日間</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">データなし:</span>
                      <span className="font-medium">{stats.users_without_data}名</span>
                    </div>
                  </div>
                </div>
              </Card>
            </div>
          </div>
        )}

        {/* 主要機能 */}
        <div>
          <h2 className="text-lg font-medium text-gray-900 mb-4">主要機能</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <Card 
              title="CSVアップロード" 
              className="cursor-pointer hover:shadow-xl transition-shadow"
              onClick={() => navigate('/admin/csv-upload')}
            >
              <div className="space-y-4">
                <div className="text-center">
                  <div className="text-4xl mb-2">📤</div>
                  <p className="text-gray-600">センサデータとマッピングファイルをアップロード</p>
                </div>
                <Button variant="primary" size="sm" className="w-full">
                  アップロード画面へ
                </Button>
              </div>
            </Card>
            
            <Card 
              title="ユーザー管理" 
              className="cursor-pointer hover:shadow-xl transition-shadow"
              onClick={() => navigate('/admin/users')}
            >
              <div className="space-y-4">
                <div className="text-center">
                  <div className="text-4xl mb-2">👥</div>
                  <p className="text-gray-600">被験者アカウントの作成・管理</p>
                  {stats && (
                    <p className="text-xs text-blue-600 mt-2">
                      現在 {stats.total_users} 名登録済み
                    </p>
                  )}
                </div>
                <Button variant="primary" size="sm" className="w-full">
                  ユーザー管理画面へ
                </Button>
              </div>
            </Card>
            
            <Card 
              title="アップロード履歴" 
              className="cursor-pointer hover:shadow-xl transition-shadow"
              onClick={() => navigate('/admin/upload-history')}
            >
              <div className="space-y-4">
                <div className="text-center">
                  <div className="text-4xl mb-2">📋</div>
                  <p className="text-gray-600">過去のデータアップロード履歴を確認</p>
                  {stats && (
                    <p className="text-xs text-green-600 mt-2">
                      直近7日間: {stats.recent_uploads} 件
                    </p>
                  )}
                </div>
                <Button variant="primary" size="sm" className="w-full">
                  履歴を表示
                </Button>
              </div>
            </Card>
          </div>
        </div>

        {/* クイックアクション */}
        <Card title="クイックアクション">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Button
              variant="outline"
              onClick={() => navigate('/admin/csv-upload')}
              className="justify-start h-auto py-3"
            >
              <div className="text-left">
                <div className="flex items-center mb-1">
                  <span className="mr-2 text-lg">⚡</span>
                  <span className="font-medium">新しいデータをアップロード</span>
                </div>
                <p className="text-xs text-gray-500">センサデータの一括処理</p>
              </div>
            </Button>
            
            <Button
              variant="outline"
              onClick={() => navigate('/admin/users')}
              className="justify-start h-auto py-3"
            >
              <div className="text-left">
                <div className="flex items-center mb-1">
                  <span className="mr-2 text-lg">👥</span>
                  <span className="font-medium">ユーザーを管理</span>
                </div>
                <p className="text-xs text-gray-500">アカウント作成・編集・削除</p>
              </div>
            </Button>
            
            <Button
              variant="outline"
              onClick={() => navigate('/admin/upload-history')}
              className="justify-start h-auto py-3"
            >
              <div className="text-left">
                <div className="flex items-center mb-1">
                  <span className="mr-2 text-lg">📊</span>
                  <span className="font-medium">処理状況を確認</span>
                </div>
                <p className="text-xs text-gray-500">アップロード結果とエラー</p>
              </div>
            </Button>
          </div>
        </Card>

        {/* データ品質インジケーター */}
        {stats && (
          <Card title="データ品質" subtitle="システム全体のデータ状況">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* データカバレッジ */}
              <div className="text-center">
                <div className="relative w-24 h-24 mx-auto mb-3">
                  <svg className="w-24 h-24 transform -rotate-90" viewBox="0 0 36 36">
                    <path
                      d="M18 2.0845
                        a 15.9155 15.9155 0 0 1 0 31.831
                        a 15.9155 15.9155 0 0 1 0 -31.831"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="3"
                      className="text-gray-200"
                    />
                    <path
                      d="M18 2.0845
                        a 15.9155 15.9155 0 0 1 0 31.831
                        a 15.9155 15.9155 0 0 1 0 -31.831"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="3"
                      strokeDasharray={`${(stats.users_with_data / stats.total_users) * 100}, 100`}
                      className="text-blue-500"
                    />
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-xl font-bold text-blue-600">
                      {stats.total_users > 0 ? Math.round((stats.users_with_data / stats.total_users) * 100) : 0}%
                    </span>
                  </div>
                </div>
                <p className="text-sm font-medium text-gray-900">データカバレッジ</p>
                <p className="text-xs text-gray-500">
                  {stats.users_with_data} / {stats.total_users} ユーザー
                </p>
              </div>

              {/* アクティブ率 */}
              <div className="text-center">
                <div className="relative w-24 h-24 mx-auto mb-3">
                  <svg className="w-24 h-24 transform -rotate-90" viewBox="0 0 36 36">
                    <path
                      d="M18 2.0845
                        a 15.9155 15.9155 0 0 1 0 31.831
                        a 15.9155 15.9155 0 0 1 0 -31.831"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="3"
                      className="text-gray-200"
                    />
                    <path
                      d="M18 2.0845
                        a 15.9155 15.9155 0 0 1 0 31.831
                        a 15.9155 15.9155 0 0 1 0 -31.831"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="3"
                      strokeDasharray={`${stats.total_users > 0 ? (stats.active_users / stats.total_users) * 100 : 0}, 100`}
                      className="text-green-500"
                    />
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-xl font-bold text-green-600">
                      {stats.total_users > 0 ? Math.round((stats.active_users / stats.total_users) * 100) : 0}%
                    </span>
                  </div>
                </div>
                <p className="text-sm font-medium text-gray-900">アクティブ率</p>
                <p className="text-xs text-gray-500">
                  {stats.active_users} / {stats.total_users} ユーザー
                </p>
              </div>

              {/* 最近のアクティビティ */}
              <div className="text-center">
                <div className="w-24 h-24 mx-auto mb-3 flex items-center justify-center bg-orange-100 rounded-full">
                  <span className="text-3xl font-bold text-orange-600">
                    {stats.recent_data_count > 999 ? '999+' : stats.recent_data_count}
                  </span>
                </div>
                <p className="text-sm font-medium text-gray-900">直近データ数</p>
                <p className="text-xs text-gray-500">過去7日間の新規データ</p>
              </div>
            </div>
          </Card>
        )}

        {/* システム情報 */}
        <Card title="システム情報">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-medium text-gray-900 mb-2">🔧 管理機能</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• CSVファイルの一括アップロード</li>
                <li>• ユーザーアカウント管理</li>
                <li>• センサーマッピング管理</li>
                <li>• データ処理履歴確認</li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-medium text-gray-900 mb-2">📊 データ形式</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• センサデータ: CSV (sensor_id, timestamp, temperature)</li>
                <li>• マッピング: CSV (sensor_id, user_id, subject_name)</li>
                <li>• 最大ファイルサイズ: 10MB</li>
                <li>• 文字コード: UTF-8</li>
              </ul>
            </div>
          </div>
        </Card>
      </div>
    </Layout>
  );
};