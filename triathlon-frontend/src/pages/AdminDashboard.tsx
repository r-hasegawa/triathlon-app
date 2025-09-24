import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Layout } from '@/components/layout/Layout';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

// バックエンドのレスポンス構造に合わせた型定義
interface DashboardStats {
  users: {
    total_users: number;
    total_admins: number;
  };
  competitions: {
    total_competitions: number;
    active_competitions: number;
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
    active_mappings: number;
    mapping_rate: number;
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
                      アクティブ: {stats.competitions.active_competitions.toLocaleString()}大会
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
                      マッピング済み: {stats.mappings.active_mappings.toLocaleString()}
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
                    <p className="text-sm font-medium text-gray-600">未マッピング</p>
                    <p className="text-2xl font-bold text-orange-600">
                      {(stats.mappings.total_mappings - stats.mappings.active_mappings).toLocaleString()}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      マッピング率: {stats.mappings.mapping_rate.toFixed(1)}%
                    </p>
                  </div>
                  <div className="ml-4">
                    <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-orange-500">
                      <svg className="h-6 w-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                      </svg>
                    </div>
                  </div>
                </div>
              </Card>
            </div>

            {/* センサデータ詳細 */}
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
                  <p className="text-sm font-medium text-yellow-700 mb-1">WBGTデータ</p>
                  <p className="text-lg font-bold text-yellow-900">
                    {stats.sensor_data.wbgt.toLocaleString()}
                  </p>
                </div>
              </Card>

              <Card className="p-4 bg-purple-50 border-purple-200">
                <div className="text-center">
                  <p className="text-sm font-medium text-purple-700 mb-1">大会記録</p>
                  <p className="text-lg font-bold text-purple-900">
                    {stats.sensor_data.race_records.toLocaleString()}
                  </p>
                </div>
              </Card>
            </div>

            {/* アップロード活動統計 */}
            <Card className="p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">アップロード活動</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <p className="text-sm font-medium text-gray-600">総バッチ数</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {stats.upload_activity.total_batches.toLocaleString()}
                  </p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-600">今日のアップロード</p>
                  <p className="text-2xl font-bold text-green-600">
                    {stats.upload_activity.today_batches.toLocaleString()}
                  </p>
                </div>
              </div>
            </Card>
          </>
        )}

        {/* 管理者アクション */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <Card className="p-6 hover:shadow-lg transition-shadow cursor-pointer" 
                onClick={() => navigate('/admin/users')}>
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-600">
                  <svg className="h-6 w-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
                  </svg>
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-900">ユーザー管理</p>
                <p className="text-sm text-gray-500">ユーザーの一覧表示・詳細確認</p>
              </div>
            </div>
          </Card>

          <Card className="p-6 hover:shadow-lg transition-shadow cursor-pointer" 
                onClick={() => navigate('/admin/competitions')}>
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-green-600">
                  <svg className="h-6 w-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                  </svg>
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-900">大会管理</p>
                <p className="text-sm text-gray-500">大会の作成・編集・削除</p>
              </div>
            </div>
          </Card>

          <Card className="p-6 hover:shadow-lg transition-shadow cursor-pointer" 
                onClick={() => navigate('/admin/upload')}>
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-purple-600">
                  <svg className="h-6 w-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-900">データアップロード</p>
                <p className="text-sm text-gray-500">センサーデータ・マッピング登録</p>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </Layout>
  );
};