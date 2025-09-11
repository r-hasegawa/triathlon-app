// src/pages/UserDashboard.tsx (修正版)

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Layout } from '@/components/layout/Layout';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { userDataService } from '@/services/userDataService';
import { UserDataSummary, CompetitionDetail } from '@/types/userData';

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
      
      const summary = await userDataService.getUserDataSummary();
      setDataSummary(summary);
    } catch (error) {
      console.error('Error fetching user data:', error);
      setError('データの取得に失敗しました。マッピング済みのセンサーデータがありません。');
    } finally {
      setIsLoading(false);
    }
  };

  const handleViewCompetitionData = async (competition: CompetitionDetail) => {
    try {
      setError('');
      const data = await userDataService.getCompetitionData(competition.competition_id);
      
      // 簡単なデータ表示（後でグラフに置き換え）
      const message = `${competition.name}のデータ:\n` +
        `総データ数: ${data.total_records}件\n` +
        `センサータイプ: ${competition.mapped_sensors.map(s => s.sensor_type).join(', ')}`;
      
      alert(message);
    } catch (error) {
      setError('大会データの取得に失敗しました');
    }
  };

  const getSensorTypeDisplayName = (sensorType: string): string => {
    const sensorNames: Record<string, string> = {
      'skin_temperature': '体表温',
      'core_temperature': 'カプセル体温',
      'heart_rate': '心拍',
      'wbgt': 'WBGT'
    };
    return sensorNames[sensorType] || sensorType;
  };

  const getSensorTypeInfo = (sensorType: string) => {
    const sensorInfo: Record<string, { icon: string; color: string }> = {
      'skin_temperature': { icon: '🌡️', color: 'bg-red-100 text-red-700' },
      'core_temperature': { icon: '💊', color: 'bg-purple-100 text-purple-700' },
      'heart_rate': { icon: '❤️', color: 'bg-pink-100 text-pink-700' },
      'wbgt': { icon: '🌤️', color: 'bg-yellow-100 text-yellow-700' }
    };
    return sensorInfo[sensorType] || { icon: '📊', color: 'bg-gray-100 text-gray-700' };
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
            こんにちは、{user?.full_name || user?.username || 'ユーザー'}さん
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

        {/* データなしの場合 */}
        {!dataSummary || dataSummary.total_records === 0 ? (
          <Card className="p-8 text-center">
            <div className="text-gray-400 text-6xl mb-4">📊</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">センサーデータがありません</h3>
            <p className="text-gray-500 mb-4">
              まだセンサーデータがマッピングされていません。<br/>
              大会に参加してセンサーデータが記録されると、ここに表示されます。
            </p>
            <Button onClick={fetchUserData} variant="outline">
              データを確認
            </Button>
          </Card>
        ) : (
          <>
            {/* データサマリー */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
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
                    <p className="text-sm font-medium text-gray-500">参加大会数</p>
                    <p className="text-2xl font-bold text-gray-900">{dataSummary.total_competitions}</p>
                    <p className="text-xs text-gray-500">データ記録済み大会</p>
                  </div>
                </div>
              </Card>

              {/* センサータイプ数 */}
              <Card className="p-6">
                <div className="flex items-center">
                  <div className="p-3 rounded-full bg-purple-100">
                    <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                    </svg>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">センサータイプ</p>
                    <p className="text-2xl font-bold text-gray-900">{dataSummary.mapped_sensor_types.length}</p>
                    <p className="text-xs text-gray-500">種類のセンサー</p>
                  </div>
                </div>
              </Card>
            </div>

            {/* 参加大会詳細 */}
            <Card className="p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">参加大会</h2>
              <div className="space-y-4">
                {dataSummary.competitions.map((competition) => (
                  <div key={competition.competition_id} className="p-4 bg-gray-50 rounded-lg">
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        <h3 className="font-medium text-gray-900">{competition.name}</h3>
                        {competition.location && (
                          <p className="text-sm text-gray-500">📍 {competition.location}</p>
                        )}
                        <p className="text-sm text-gray-600">
                          データ数: {competition.total_records}件
                          {competition.has_race_record && <span className="ml-2 text-green-600">🏃 レース記録あり</span>}
                        </p>
                      </div>
                      <Button 
                        onClick={() => handleViewCompetitionData(competition)}
                        size="sm"
                      >
                        データを見る
                      </Button>
                    </div>
                    
                    {/* センサータイプ表示 */}
                    <div className="flex flex-wrap gap-2">
                      {competition.mapped_sensors.map((sensor, index) => {
                        const info = getSensorTypeInfo(sensor.sensor_type);
                        return (
                          <div key={index} className={`px-3 py-1 rounded-full text-sm ${info.color}`}>
                            {info.icon} {getSensorTypeDisplayName(sensor.sensor_type)} ({sensor.total_records}件)
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </>
        )}

        {/* データ更新ボタン */}
        <Card className="p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">アクション</h2>
          <div className="flex gap-4">
            <Button onClick={fetchUserData}>データ更新</Button>
            <Button variant="outline" disabled>グラフ表示 (開発中)</Button>
          </div>
        </Card>
      </div>
    </Layout>
  );
};