/**
 * UserDashboard.tsx - 新システム対応版
 * マルチセンサーシステムに対応した被験者ダッシュボード
 */

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Layout } from '@/components/layout/Layout';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

// 新システム用のダミーデータ（後で実際のAPIに置き換え）
interface UserDataSummary {
  total_records: number;
  competitions: string[];
  sensor_types: string[];
  latest_data_date: string | null;
  data_quality: 'good' | 'fair' | 'poor';
}

export const UserDashboard: React.FC = () => {
  const { user } = useAuth();
  const [dataSummary, setDataSummary] = useState<UserDataSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchUserData();
  }, []);

  const fetchUserData = async () => {
    try {
      setIsLoading(true);
      setError('');
      
      // TODO: 新システムのAPIエンドポイントを実装後に置き換え
      // 現在はダミーデータを表示
      await new Promise(resolve => setTimeout(resolve, 1000)); // 模擬的な遅延
      
      setDataSummary({
        total_records: 12, // サンプルデータから
        competitions: ['2025年トライアスロン大会'],
        sensor_types: ['体表温'],
        latest_data_date: new Date().toISOString(),
        data_quality: 'good'
      });
    } catch (error) {
      console.error('Error fetching user data:', error);
      setError('データの取得に失敗しました');
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <Layout>
        <div className="flex justify-center items-center py-12">
          <LoadingSpinner size="lg" />
          <span className="ml-3 text-gray-600">データを読み込み中...</span>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-8">
        {/* ウェルカムヘッダー */}
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-lg p-6 text-white">
          <h1 className="text-2xl font-bold mb-2">
            こんにちは、{user?.username || user?.full_name || 'ユーザー'}さん
          </h1>
          <p className="text-blue-100">
            あなたのセンサーデータ状況をご確認いただけます
          </p>
        </div>

        {/* エラー表示 */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex justify-between items-center">
              <p className="text-sm text-red-600">{error}</p>
              <Button onClick={fetchUserData} variant="outline" size="sm">
                再試行
              </Button>
            </div>
          </div>
        )}

        {/* データサマリー */}
        {dataSummary && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* 総データ数 */}
            <Card className="p-6">
              <div className="flex items-center">
                <div className="p-3 rounded-full bg-blue-100">
                  <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">総データ数</p>
                  <p className="text-2xl font-bold text-gray-900">{dataSummary.total_records}</p>
                  <p className="text-xs text-gray-500">記録されたデータポイント</p>
                </div>
              </div>
            </Card>

            {/* 参加大会数 */}
            <Card className="p-6">
              <div className="flex items-center">
                <div className="p-3 rounded-full bg-green-100">
                  <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                  </svg>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">参加大会</p>
                  <p className="text-2xl font-bold text-gray-900">{dataSummary.competitions.length}</p>
                  <p className="text-xs text-gray-500">大会でのデータ記録</p>
                </div>
              </div>
            </Card>

            {/* センサー種類 */}
            <Card className="p-6">
              <div className="flex items-center">
                <div className="p-3 rounded-full bg-purple-100">
                  <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
                  </svg>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">センサー種類</p>
                  <p className="text-2xl font-bold text-gray-900">{dataSummary.sensor_types.length}</p>
                  <p className="text-xs text-gray-500">使用されたセンサータイプ</p>
                </div>
              </div>
            </Card>

            {/* データ品質 */}
            <Card className="p-6">
              <div className="flex items-center">
                <div className={`p-3 rounded-full ${
                  dataSummary.data_quality === 'good' ? 'bg-green-100' :
                  dataSummary.data_quality === 'fair' ? 'bg-yellow-100' : 'bg-red-100'
                }`}>
                  <svg className={`w-6 h-6 ${
                    dataSummary.data_quality === 'good' ? 'text-green-600' :
                    dataSummary.data_quality === 'fair' ? 'text-yellow-600' : 'text-red-600'
                  }`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">データ品質</p>
                  <p className={`text-2xl font-bold ${
                    dataSummary.data_quality === 'good' ? 'text-green-600' :
                    dataSummary.data_quality === 'fair' ? 'text-yellow-600' : 'text-red-600'
                  }`}>
                    {dataSummary.data_quality === 'good' ? '良好' :
                     dataSummary.data_quality === 'fair' ? '普通' : '要改善'}
                  </p>
                  <p className="text-xs text-gray-500">データ整合性</p>
                </div>
              </div>
            </Card>
          </div>
        )}

        {/* 参加大会詳細 */}
        {dataSummary && dataSummary.competitions.length > 0 && (
          <Card className="p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">参加大会</h2>
            <div className="space-y-3">
              {dataSummary.competitions.map((competition, index) => (
                <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center">
                    <div className="p-2 bg-blue-100 rounded-full mr-3">
                      <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                      </svg>
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">{competition}</p>
                      <p className="text-sm text-gray-500">センサーデータ記録済み</p>
                    </div>
                  </div>
                  <Button variant="outline" size="sm" disabled>
                    詳細表示 (準備中)
                  </Button>
                </div>
              ))}
            </div>
          </Card>
        )}

        {/* センサータイプ詳細 */}
        {dataSummary && dataSummary.sensor_types.length > 0 && (
          <Card className="p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">記録済みセンサータイプ</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {dataSummary.sensor_types.map((sensorType, index) => {
                const sensorInfo: Record<string, { icon: string; name: string; color: string }> = {
                  '体表温': { icon: '🌡️', name: '体表温度', color: 'bg-red-100 text-red-700' },
                  'カプセル体温': { icon: '💊', name: 'カプセル体温', color: 'bg-purple-100 text-purple-700' },
                  '心拍': { icon: '❤️', name: '心拍数', color: 'bg-pink-100 text-pink-700' },
                  'WBGT': { icon: '🌤️', name: '環境データ', color: 'bg-yellow-100 text-yellow-700' }
                };
                
                const info = sensorInfo[sensorType] || { icon: '📊', name: sensorType, color: 'bg-gray-100 text-gray-700' };
                
                return (
                  <div key={index} className={`p-4 rounded-lg ${info.color}`}>
                    <div className="text-2xl mb-2">{info.icon}</div>
                    <p className="font-medium">{info.name}</p>
                    <p className="text-xs opacity-75">データ記録済み</p>
                  </div>
                );
              })}
            </div>
          </Card>
        )}

        {/* クイックアクション */}
        <Card className="p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">アクション</h2>
          <div className="flex gap-4">
            <Button variant="outline" disabled>データ表示 (準備中)</Button>
            <Button variant="outline" disabled>グラフ表示 (準備中)</Button>
            <Button onClick={fetchUserData}>データ更新</Button>
          </div>
        </Card>
      </div>
    </Layout>
  );
};