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
                      {stats.users.total.toLocaleString()}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      管理者: {stats.users.admin_users.toLocaleString()}名 / 一般: {stats.users.general_users.toLocaleString()}名
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
                    <p className="text-2xl font-bold text-green-600">
                      {stats.competitions.total.toLocaleString()}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      開催済み・予定含む
                    </p>
                  </div>
                  <div className="ml-4">
                    <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-green-500">
                      <svg className="h-6 w-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
                      </svg>
                    </div>
                  </div>
                </div>
              </Card>

              <Card className="p-6">
                <div className="flex items-center">
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-600">総センサーデータ</p>
                    <p className="text-2xl font-bold text-purple-600">
                      {stats.sensor_data.total.toLocaleString()}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      体表温・カプセル・心拍・WBGT
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
                    <p className="text-2xl font-bold text-indigo-600">
                      {stats.mappings.total.toLocaleString()}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      センサーとユーザーの関連付け
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
                    {stats.race_records.total.toLocaleString()}
                  </p>
                </div>
              </Card>
            </div>

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
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
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
                  onClick={() => navigate('/admin/mappings')}
                  className="flex items-center justify-center p-4 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200"
                  variant="outline"
                >
                  <svg className="h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                  </svg>
                  マッピング管理
                </Button>
              </div>
            </Card>
          </>
        )}
      </div>
    </Layout>
  );
};