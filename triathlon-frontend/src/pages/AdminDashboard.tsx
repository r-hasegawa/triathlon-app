import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Layout } from '@/components/layout/Layout';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

interface DashboardStats {
  total_users: number;
  active_users: number;
  total_competitions: number;
  active_competitions: number;
  total_sensor_records: number;
  mapped_sensor_records: number;
  unmapped_sensor_records: number;
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
        <div className="bg-gradient-to-r from-purple-600 to-purple-700 rounded-lg p-8">
          <h1 className="text-3xl font-bold text-white mb-2">管理者ダッシュボード</h1>
          <p className="text-purple-100">実データ形式対応システム v3.0</p>
        </div>

        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card className="p-6">
              <div className="text-center">
                <p className="text-sm font-medium text-gray-600">総ユーザー数</p>
                <p className="text-2xl font-bold text-gray-900">{stats.total_users}</p>
                <p className="text-xs text-gray-500">アクティブ: {stats.active_users}</p>
              </div>
            </Card>

            <Card className="p-6">
              <div className="text-center">
                <p className="text-sm font-medium text-gray-600">総大会数</p>
                <p className="text-2xl font-bold text-gray-900">{stats.total_competitions}</p>
                <p className="text-xs text-gray-500">アクティブ: {stats.active_competitions}</p>
              </div>
            </Card>

            <Card className="p-6">
              <div className="text-center">
                <p className="text-sm font-medium text-gray-600">センサーレコード</p>
                <p className="text-2xl font-bold text-gray-900">{stats.total_sensor_records.toLocaleString()}</p>
                <p className="text-xs text-gray-500">マッピング済み: {stats.mapped_sensor_records.toLocaleString()}</p>
              </div>
            </Card>

            <Card className="p-6">
              <div className="text-center">
                <p className="text-sm font-medium text-gray-600">未マッピング</p>
                <p className="text-2xl font-bold text-gray-900">{stats.unmapped_sensor_records.toLocaleString()}</p>
                <p className="text-xs text-gray-500">要処理データ</p>
              </div>
            </Card>
          </div>
        )}

        {/* 🆕 管理機能ナビゲーション */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <Card className="p-6 hover:shadow-lg transition-shadow">
            <div className="text-center">
              <div className="mx-auto w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">ユーザー管理</h3>
              <p className="text-sm text-gray-600 mb-4">システムユーザーの管理・権限設定</p>
              <Button onClick={() => navigate('/admin/users')} className="w-full">
                ユーザー管理へ
              </Button>
            </div>
          </Card>

          <Card className="p-6 hover:shadow-lg transition-shadow">
            <div className="text-center">
              <div className="mx-auto w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">大会管理</h3>
              <p className="text-sm text-gray-600 mb-4">大会の作成・編集・削除</p>
              <Button onClick={() => navigate('/admin/competitions')} className="w-full">
                大会管理へ
              </Button>
            </div>
          </Card>

          {/* 🆕 新しいアップロード画面へのリンク */}
          <Card className="p-6 hover:shadow-lg transition-shadow border-2 border-purple-200 bg-purple-50">
            <div className="text-center">
              <div className="mx-auto w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-purple-900 mb-2">🆕 実データアップロード</h3>
              <p className="text-sm text-purple-700 mb-4">halshare・e-Celcius・TCX形式対応</p>
              <Button 
                onClick={() => navigate('/sensor-data-upload')} 
                className="w-full bg-purple-600 hover:bg-purple-700"
              >
                新アップロード画面へ
              </Button>
            </div>
          </Card>
        </div>

        {/* 🔄 既存のアップロード画面へのリンク（互換性維持） */}
        <Card className="p-6 bg-gray-50">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">従来のアップロード機能</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Button 
              onClick={() => navigate('/multi-sensor/upload')} 
              variant="outline"
              className="w-full"
            >
              従来のマルチセンサーアップロード
            </Button>
            <Button 
              onClick={() => navigate('/multi-sensor/status')} 
              variant="outline"
              className="w-full"
            >
              データ状況確認
            </Button>
          </div>
          <p className="text-xs text-gray-500 mt-2">
            ※ 新しい実データアップロード機能をご利用ください
          </p>
        </Card>

        {/* クイックアクション */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">クイックアクション</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Button 
              onClick={() => window.open('/docs', '_blank')} 
              variant="outline"
              className="w-full"
            >
              API ドキュメント
            </Button>
            <Button 
              onClick={fetchStats} 
              variant="outline"
              className="w-full"
            >
              統計データ更新
            </Button>
            <Button 
              onClick={() => navigate('/admin/system-logs')} 
              variant="outline"
              className="w-full"
              disabled
            >
              システムログ（準備中）
            </Button>
          </div>
        </Card>
      </div>
    </Layout>
  );
};