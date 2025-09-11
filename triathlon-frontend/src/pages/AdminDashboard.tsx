/**
 * AdminDashboard.tsx - クリーン版
 */

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
              </div>
            </Card>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">ユーザー管理</h3>
            <p className="text-sm text-gray-600 mb-4">システムユーザーの管理</p>
            <Button onClick={() => navigate('/admin/users')} className="w-full">
              ユーザー管理へ
            </Button>
          </Card>

          <Card className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">大会管理</h3>
            <p className="text-sm text-gray-600 mb-4">大会の作成・編集・削除</p>
            <Button onClick={() => navigate('/admin/competitions')} className="w-full">
              大会管理へ
            </Button>
          </Card>

          <Card className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">データアップロード</h3>
            <p className="text-sm text-gray-600 mb-4">センサーデータのアップロード</p>
            <Button onClick={() => navigate('/multi-sensor/upload')} className="w-full">
              アップロードへ
            </Button>
          </Card>
        </div>
      </div>
    </Layout>
  );
};