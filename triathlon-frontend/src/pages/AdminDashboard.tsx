import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Layout } from '@/components/layout/Layout';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

// 実際のAPIレスポンス構造に合わせた型定義
interface DashboardStats {
  users: {
    general_users: number;
    admin_users: number;
    total: number;
  };
  competitions: {
    total: number;
  };
  sensor_data: {
    skin_temperature: number;
    core_temperature: number;
    heart_rate: number;
    wbgt: number;
    total: number;
  };
  race_records: {
    total: number;
  };
  mappings: {
    total: number;
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
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/admin/stats`, {
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
            <Button
              onClick={fetchStats}
              className="mt-4"
              variant="outline"
            >
              再読み込み
            </Button>
          </div>
        </Card>
      </Layout>
    );
  }

  if (!stats) {
    return (
      <Layout>
        <Card className="p-6">
          <p className="text-gray-500 text-center">データがありません</p>
        </Card>
      </Layout>
    );
  }

  return (
    <Layout maxWidth="wide">
      <div className="space-y-6">
        {/* ヘッダー */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">管理者ダッシュボード</h2>
            <p className="text-sm text-gray-500 mt-1">システム全体の統計情報</p>
          </div>
          <Button
            onClick={fetchStats}
            variant="outline"
            size="sm"
            className="flex items-center gap-2"
          >
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            更新
          </Button>
        </div>

        {/* メイン統計カード */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* ユーザー数 */}
          <Card className="p-6 bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-blue-700 mb-1">総ユーザー数</p>
                <p className="text-3xl font-bold text-blue-900">{stats.users.total}</p>
                <div className="mt-2 space-y-1">
                  <p className="text-xs text-blue-600">一般: {stats.users.general_users}</p>
                  <p className="text-xs text-blue-600">管理者: {stats.users.admin_users}</p>
                </div>
              </div>
              <div className="p-3 bg-blue-200 rounded-lg">
                <svg className="h-6 w-6 text-blue-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
            </div>
          </Card>

          {/* 大会数 */}
          <Card className="p-6 bg-gradient-to-br from-green-50 to-green-100 border-green-200">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-green-700 mb-1">登録大会数</p>
                <p className="text-3xl font-bold text-green-900">{stats.competitions.total}</p>
              </div>
              <div className="p-3 bg-green-200 rounded-lg">
                <svg className="h-6 w-6 text-green-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
          </Card>

          {/* センサーデータ総数 */}
          <Card className="p-6 bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-purple-700 mb-1">センサーデータ</p>
                <p className="text-3xl font-bold text-purple-900">{stats.sensor_data.total.toLocaleString()}</p>
              </div>
              <div className="p-3 bg-purple-200 rounded-lg">
                <svg className="h-6 w-6 text-purple-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
              </div>
            </div>
          </Card>

          {/* マッピング数 */}
          <Card className="p-6 bg-gradient-to-br from-orange-50 to-orange-100 border-orange-200">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-orange-700 mb-1">マッピング数</p>
                <p className="text-3xl font-bold text-orange-900">{stats.mappings.total}</p>
              </div>
              <div className="p-3 bg-orange-200 rounded-lg">
                <svg className="h-6 w-6 text-orange-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                </svg>
              </div>
            </div>
          </Card>
        </div>

        {/* センサーデータ詳細 */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            センサーデータ詳細
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
            <Card className="p-4 bg-red-50 border-red-200">
              <div className="text-center">
                <p className="text-sm font-medium text-red-700 mb-1">体表温</p>
                <p className="text-lg font-bold text-red-900">
                  {stats.sensor_data.skin_temperature.toLocaleString()}
                </p>
              </div>
            </Card>

            <Card className="p-4 bg-pink-50 border-pink-200">
              <div className="text-center">
                <p className="text-sm font-medium text-pink-700 mb-1">カプセル温</p>
                <p className="text-lg font-bold text-pink-900">
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
                  {stats.race_records.total.toLocaleString()}
                </p>
              </div>
            </Card>
          </div>
        </Card>

        {/* クイックアクション */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            よく使う機能
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <Button
              onClick={() => navigate('/admin/users')}
              className="flex flex-col items-center justify-center p-6 bg-white hover:bg-gray-50 text-gray-700 border-2 border-gray-200 hover:border-blue-300 h-auto"
              variant="outline"
            >
              <svg className="h-8 w-8 mb-2 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
              <span className="font-medium">ユーザー詳細管理</span>
              <span className="text-xs text-gray-500 mt-1">フィードバック確認</span>
            </Button>

            <Button
              onClick={() => navigate('/admin/competitions')}
              className="flex flex-col items-center justify-center p-6 bg-white hover:bg-gray-50 text-gray-700 border-2 border-gray-200 hover:border-green-300 h-auto"
              variant="outline"
            >
              <svg className="h-8 w-8 mb-2 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className="font-medium">大会管理</span>
              <span className="text-xs text-gray-500 mt-1">大会作成・編集</span>
            </Button>

            <Button
              onClick={() => navigate('/admin/upload')}
              className="flex flex-col items-center justify-center p-6 bg-white hover:bg-gray-50 text-gray-700 border-2 border-gray-200 hover:border-purple-300 h-auto"
              variant="outline"
            >
              <svg className="h-8 w-8 mb-2 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              <span className="font-medium">データアップロード</span>
              <span className="text-xs text-gray-500 mt-1">各種センサーデータ</span>
            </Button>
          </div>
        </Card>

      </div>
    </Layout>
  );
};