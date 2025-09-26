import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Layout } from '@/components/layout/Layout';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

// シンプル化された統計情報の型定義
interface DashboardStats {
  users: {
    total_users: number;
    total_admins: number;
  };
  competitions: {
    total_competitions: number;
  };
  sensor_data: {
    skin_temperature: number;
    core_temperature: number;
    heart_rate: number;
    wbgt: number;
    race_records: number;
    total_records: number;
  };
  mappings: {
    total_mappings: number;
    mapped_sensors: number;         // 新規：ユニークなセンサー数
    users_with_mappings: number;    // 新規：マッピングを持つユーザー数
  };
  upload_activity: {
    total_batches: number;
    today_batches: number;
  };
}

export const AdminDashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      setIsLoading(true);
      setError('');
      
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:8000/admin/stats', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
      }

      const data = await response.json();
      console.log('AdminDashboard stats:', data);
      setStats(data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
      setError('統計データの取得に失敗しました');
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <Layout>
        <div className="flex justify-center items-center py-12">
          <LoadingSpinner size="lg" />
        </div>
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout>
        <Card className="p-6 border-red-200 bg-red-50">
          <div className="text-red-700 text-center">
            <p className="font-medium">エラーが発生しました</p>
            <p className="text-sm mt-1">{error}</p>
            <Button onClick={fetchStats} className="mt-3">
              再読み込み
            </Button>
          </div>
        </Card>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-8">
        {/* ヘッダー */}
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-lg p-8">
          <h1 className="text-3xl font-bold text-white mb-2">
            管理者ダッシュボード
          </h1>
          <p className="text-blue-100">
            システム全体の統計情報と管理機能
          </p>
        </div>

        {/* システム統計 */}
        {stats && (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <Card className="p-6">
                <div className="flex items-center">
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-600">総ユーザー数</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {stats.users.total_users.toLocaleString()}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      管理者: {stats.users.total_admins.toLocaleString()}名
                    </p>
                  </div>
                  <div className="ml-4">
                    <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-blue-500">
                      <svg className="h-6 w-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
                      </svg>
                    </div>
                  </div>
                </div>
              </Card>

              <Card className="p-6">
                <div className="flex items-center">
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-600">総大会数</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {stats.competitions.total_competitions.toLocaleString()}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      登録済み大会
                    </p>
                  </div>
                  <div className="ml-4">
                    <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-green-500">
                      <svg className="h-6 w-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                      </svg>
                    </div>
                  </div>
                </div>
              </Card>

              <Card className="p-6">
                <div className="flex items-center">
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-600">総センサー記録</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {stats.sensor_data.total_records.toLocaleString()}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      全センサーデータ合計
                    </p>
                  </div>
                  <div className="ml-4">
                    <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-purple-500">
                      <svg className="h-6 w-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                      </svg>
                    </div>
                  </div>
                </div>
              </Card>

              <Card className="p-6">
                <div className="flex items-center">
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-600">センサーマッピング</p>
                    <p className="text-2xl font-bold text-blue-600">
                      {stats.mappings.total_mappings.toLocaleString()}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      ユニークセンサー: {stats.mappings.mapped_sensors.toLocaleString()}個
                    </p>
                  </div>
                  <div className="ml-4">
                    <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-indigo-500">
                      <svg className="h-6 w-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                      </svg>
                    </div>
                  </div>
                </div>
              </Card>
            </div>

            {/* センサーデータ詳細 */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
              <Card className="p-4 bg-red-50 border-red-200">
                <div className="text-center">
                  <p className="text-sm font-medium text-red-700 mb-1">体表温データ</p>
                  <p className="text-lg font-bold text-red-900">
                    {stats.sensor_data.skin_temperature.toLocaleString()}
                  </p>
                </div>
              </Card>

              <Card className="p-4 bg-blue-50 border-blue-200">
                <div className="text-center">
                  <p className="text-sm font-medium text-blue-700 mb-1">カプセル体温</p>
                  <p className="text-lg font-bold text-blue-900">
                    {stats.sensor_data.core_temperature.toLocaleString()}
                  </p>
                </div>
              </Card>

              <Card className="p-4 bg-green-50 border-green-200">
                <div className="text-center">
                  <p className="text-sm font-medium text-green-700 mb-1">心拍データ</p>
                  <p className="text-lg font-bold text-green-900">
                    {stats.sensor_data.heart_rate.toLocaleString()}
                  </p>
                </div>
              </Card>

              <Card className="p-4 bg-yellow-50 border-yellow-200">
                <div className="text-center">
                  <p className="text-sm font-medium text-yellow-700 mb-1">WBGT環境</p>
                  <p className="text-lg font-bold text-yellow-900">
                    {stats.sensor_data.wbgt.toLocaleString()}
                  </p>
                </div>
              </Card>

              <Card className="p-4 bg-gray-50 border-gray-200">
                <div className="text-center">
                  <p className="text-sm font-medium text-gray-700 mb-1">大会記録</p>
                  <p className="text-lg font-bold text-gray-900">
                    {stats.sensor_data.race_records.toLocaleString()}
                  </p>
                </div>
              </Card>
            </div>

            {/* マッピング詳細統計 */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <Card className="p-6">
                <div className="text-center">
                  <p className="text-sm font-medium text-gray-600 mb-2">総マッピング数</p>
                  <p className="text-3xl font-bold text-blue-600">
                    {stats.mappings.total_mappings.toLocaleString()}
                  </p>
                  <p className="text-xs text-gray-500 mt-2">
                    センサーとユーザーの関連付け
                  </p>
                </div>
              </Card>

              <Card className="p-6">
                <div className="text-center">
                  <p className="text-sm font-medium text-gray-600 mb-2">マッピング済みセンサー</p>
                  <p className="text-3xl font-bold text-purple-600">
                    {stats.mappings.mapped_sensors.toLocaleString()}
                  </p>
                  <p className="text-xs text-gray-500 mt-2">
                    ユニークなセンサー数
                  </p>
                </div>
              </Card>

              <Card className="p-6">
                <div className="text-center">
                  <p className="text-sm font-medium text-gray-600 mb-2">マッピング保有ユーザー</p>
                  <p className="text-3xl font-bold text-green-600">
                    {stats.mappings.users_with_mappings.toLocaleString()}
                  </p>
                  <p className="text-xs text-gray-500 mt-2">
                    1つ以上のセンサーを持つユーザー
                  </p>
                </div>
              </Card>
            </div>

            {/* アップロード活動 */}
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                アップロード活動
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="text-center">
                  <p className="text-sm font-medium text-gray-600 mb-2">総アップロードバッチ</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {stats.upload_activity.total_batches.toLocaleString()}
                  </p>
                </div>
                <div className="text-center">
                  <p className="text-sm font-medium text-gray-600 mb-2">本日のアップロード</p>
                  <p className="text-2xl font-bold text-green-600">
                    {stats.upload_activity.today_batches.toLocaleString()}
                  </p>
                </div>
              </div>
            </Card>

            {/* 管理機能ナビゲーション */}
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                管理機能
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <Button
                  onClick={() => navigate('/admin/users')}
                  className="flex items-center justify-center p-4 bg-blue-50 hover:bg-blue-100 text-blue-700 border border-blue-200"
                  variant="outline"
                >
                  <svg className="h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
                  </svg>
                  ユーザー管理
                </Button>

                <Button
                  onClick={() => navigate('/admin/competitions')}
                  className="flex items-center justify-center p-4 bg-green-50 hover:bg-green-100 text-green-700 border border-green-200"
                  variant="outline"
                >
                  <svg className="h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                  </svg>
                  大会管理
                </Button>

                <Button
                  onClick={() => navigate('/admin/upload')}
                  className="flex items-center justify-center p-4 bg-purple-50 hover:bg-purple-100 text-purple-700 border border-purple-200"
                  variant="outline"
                >
                  <svg className="h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                  データアップロード
                </Button>

                <Button
                  onClick={() => navigate('/admin/sensor-coverage')}
                  className="flex items-center justify-center p-4 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200"
                  variant="outline"
                >
                  <svg className="h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                  センサーカバレッジ
                </Button>
              </div>
            </Card>
          </>
        )}
      </div>
    </Layout>
  );
};