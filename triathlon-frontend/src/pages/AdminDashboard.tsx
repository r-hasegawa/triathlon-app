/**
 * AdminDashboard.tsx - 新システム対応版
 * マルチセンサーシステムに対応した管理者ダッシュボード
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Layout } from '@/components/layout/Layout';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { adminService } from '@/services/adminService';

interface DashboardStats {
  total_users: number;
  active_users: number;
  total_competitions: number;
  active_competitions: number;
  total_sensor_records: number;
  mapped_sensor_records: number;
  unmapped_sensor_records: number;
}

interface UnmappedSummary {
  total_unmapped_records: number;
  by_sensor_type: Record<string, {
    total_records: number;
    unique_sensors: number;
    sensor_ids: string[];
  }>;
}

export const AdminDashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [unmappedSummary, setUnmappedSummary] = useState<UnmappedSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setIsLoading(true);
      setError('');
      
      // 並列でデータを取得
      const [statsData, unmappedData] = await Promise.all([
        adminService.getSystemStats(),
        adminService.getUnmappedDataSummary()
      ]);
      
      setStats(statsData);
      setUnmappedSummary(unmappedData);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      setError('ダッシュボードデータの取得に失敗しました');
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <Layout>
        <div className="flex justify-center items-center py-12">
          <LoadingSpinner size="lg" />
          <span className="ml-3 text-gray-600">ダッシュボードを読み込み中...</span>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-8">
        {/* ヘッダー */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">管理者ダッシュボード</h1>
            <p className="text-gray-600 mt-1">システム全体の状況とマルチセンサーデータ管理</p>
          </div>
          <Button onClick={fetchDashboardData} variant="outline">
            🔄 更新
          </Button>
        </div>

        {/* エラー表示 */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex justify-between items-center">
              <p className="text-sm text-red-600">{error}</p>
              <Button onClick={fetchDashboardData} variant="outline" size="sm">
                再試行
              </Button>
            </div>
          </div>
        )}

        {/* システム統計カード */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* ユーザー統計 */}
            <Card className="p-6">
              <div className="flex items-center">
                <div className="p-3 rounded-full bg-blue-100">
                  <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
                  </svg>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">総ユーザー数</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.total_users}</p>
                  <p className="text-xs text-gray-500">
                    アクティブ: {stats.active_users} / 非アクティブ: {stats.total_users - stats.active_users}
                  </p>
                </div>
              </div>
            </Card>

            {/* 大会統計 */}
            <Card className="p-6">
              <div className="flex items-center">
                <div className="p-3 rounded-full bg-green-100">
                  <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                  </svg>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">総大会数</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.total_competitions}</p>
                  <p className="text-xs text-gray-500">
                    アクティブ: {stats.active_competitions}
                  </p>
                </div>
              </div>
            </Card>

            {/* センサーデータ統計 */}
            <Card className="p-6">
              <div className="flex items-center">
                <div className="p-3 rounded-full bg-purple-100">
                  <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">総データ数</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {stats.total_sensor_records.toLocaleString()}
                  </p>
                  <p className="text-xs text-gray-500">
                    マッピング済み: {stats.mapped_sensor_records.toLocaleString()}
                  </p>
                </div>
              </div>
            </Card>

            {/* 未マッピングデータ統計 */}
            <Card className="p-6">
              <div className="flex items-center">
                <div className="p-3 rounded-full bg-orange-100">
                  <svg className="w-6 h-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.732 18.5c-.77.833.192 2.5 1.732 2.5z" />
                  </svg>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">未マッピング</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {stats.unmapped_sensor_records.toLocaleString()}
                  </p>
                  <p className="text-xs text-gray-500">
                    要対応データ
                  </p>
                </div>
              </div>
            </Card>
          </div>
        )}

        {/* 未マッピングデータ詳細 */}
        {unmappedSummary && unmappedSummary.total_unmapped_records > 0 && (
          <Card className="p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-xl font-semibold text-gray-900">未マッピングデータ詳細</h2>
                <p className="text-gray-600">センサー種別ごとの未処理データ状況</p>
              </div>
              <Button
                onClick={() => navigate('/admin/multi-sensor')}
                className="bg-orange-600 hover:bg-orange-700"
              >
                マッピング処理に移動
              </Button>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Object.entries(unmappedSummary.by_sensor_type).map(([sensorType, data]) => {
                const icons: Record<string, string> = {
                  skin_temperature: '🌡️',
                  core_temperature: '💊',
                  heart_rate: '❤️',
                  wbgt: '🌤️'
                };
                
                const names: Record<string, string> = {
                  skin_temperature: '体表温',
                  core_temperature: 'カプセル体温',
                  heart_rate: '心拍',
                  wbgt: 'WBGT'
                };

                return (
                  <div key={sensorType} className="text-center p-4 bg-orange-50 rounded-lg border border-orange-200">
                    <div className="text-2xl mb-2">{icons[sensorType] || '📊'}</div>
                    <div className="text-xl font-bold text-orange-700">
                      {data.total_records}
                    </div>
                    <div className="text-sm text-gray-600">{names[sensorType] || sensorType}</div>
                    <div className="text-xs text-gray-500 mt-1">
                      {data.unique_sensors} センサー
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
              <p className="text-sm text-yellow-800">
                ⚠️ 未マッピングデータは被験者に表示されません。マルチセンサーアップロードページでマッピングを実行してください。
              </p>
            </div>
          </Card>
        )}

        {/* クイックアクション */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">クイックアクション</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Button
              onClick={() => navigate('/admin/multi-sensor')}
              className="h-20 flex flex-col items-center justify-center"
              variant="outline"
            >
              <svg className="w-6 h-6 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              <span className="text-sm">マルチセンサーアップロード</span>
            </Button>

            <Button
              onClick={() => navigate('/admin/users')}
              className="h-20 flex flex-col items-center justify-center"
              variant="outline"
            >
              <svg className="w-6 h-6 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
              </svg>
              <span className="text-sm">ユーザー管理</span>
            </Button>

            <Button
              onClick={() => navigate('/admin/competitions')}
              className="h-20 flex flex-col items-center justify-center"
              variant="outline"
            >
              <svg className="w-6 h-6 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
              <span className="text-sm">大会管理</span>
            </Button>

            <Button
              onClick={fetchDashboardData}
              className="h-20 flex flex-col items-center justify-center"
              variant="outline"
            >
              <svg className="w-6 h-6 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              <span className="text-sm">データ更新</span>
            </Button>
          </div>
        </Card>

        {/* システム情報 */}
        <Card className="p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">システム情報</h2>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">バージョン</span>
              <span className="font-medium">v2.0.0</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">稼働状況</span>
              <span className="text-green-600 font-medium">正常</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">マッピング率</span>
              <span className="font-medium">
                {stats ? Math.round((stats.mapped_sensor_records / Math.max(stats.total_sensor_records, 1)) * 100) : 0}%
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">ユーザー稼働率</span>
              <span className="font-medium">
                {stats ? Math.round((stats.active_users / Math.max(stats.total_users, 1)) * 100) : 0}%
              </span>
            </div>
          </div>
        </Card>
      </div>
    </Layout>
  );
};