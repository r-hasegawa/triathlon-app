import React, { useState, useEffect } from 'react';
import { Layout } from '@/components/layout/Layout';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { useAuth } from '@/contexts/AuthContext';

interface UserStats {
  total_sensor_records: number;
  latest_competition: string | null;
  mapped_sensors: number;
  recent_uploads: any[];
}

export const UserDashboard: React.FC = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState<UserStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchUserStats();
  }, []);

  const fetchUserStats = async () => {
    try {
      setIsLoading(true);
      setError('');
      
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:8000/me/stats', {
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
      console.error('Failed to fetch user stats:', error);
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
            <Button onClick={fetchUserStats} className="mt-3">
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
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-lg p-8">
          <h1 className="text-3xl font-bold text-white mb-2">
            ダッシュボード
          </h1>
          <p className="text-blue-100">
            {user?.username ? `${user.username}さん、` : ''}お疲れ様です
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-2">総センサーデータ数</h3>
            <p className="text-3xl font-bold text-blue-600">
              {stats?.total_sensor_records.toLocaleString() || 0}
            </p>
            <p className="text-sm text-gray-600">記録</p>
          </Card>

          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-2">マッピング済みセンサー</h3>
            <p className="text-3xl font-bold text-green-600">
              {stats?.mapped_sensors || 0}
            </p>
            <p className="text-sm text-gray-600">個</p>
          </Card>

          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-2">最新参加大会</h3>
            <p className="text-lg font-semibold text-gray-800">
              {stats?.latest_competition || '未参加'}
            </p>
          </Card>
        </div>

        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">クイックアクション</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Button
              onClick={() => window.location.href = '/data-detail'}
              className="h-16 text-left"
            >
              <div>
                <div className="font-semibold">センサーデータ詳細</div>
                <div className="text-sm opacity-75">データを確認する</div>
              </div>
            </Button>
            
            <Button
              variant="outline"
              onClick={() => window.location.href = '/feedback'}
              className="h-16 text-left"
            >
              <div>
                <div className="font-semibold">フィードバックグラフ</div>
                <div className="text-sm opacity-75">パフォーマンスを確認</div>
              </div>
            </Button>
          </div>
        </Card>
      </div>
    </Layout>
  );
};