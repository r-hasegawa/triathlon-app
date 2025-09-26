// src/pages/UserDetail.tsx - 完全修正版

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Layout } from '@/components/layout/Layout';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

// 🔄 実際のAPIレスポンス構造に合わせて修正
interface UserDataSummary {
  user_id: string;
  skin_temperature_records: number;
  core_temperature_records: number;
  heart_rate_records: number;
  total_competitions: number;
  competitions: Array<{
    competition_id: string;
    name: string;
    date: string;
    status: string;
  }>;
}

interface SensorData {
  sensor_type: string;
  sensor_id: string;
  record_count: number;
  latest_record: string;
  data_range: string;
}

export const UserDetail: React.FC = () => {
  const { userId } = useParams<{ userId: string }>();
  const navigate = useNavigate();
  
  const [userDataSummary, setUserDataSummary] = useState<UserDataSummary | null>(null);
  const [selectedCompetition, setSelectedCompetition] = useState<string>('');
  const [sensorData, setSensorData] = useState<SensorData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (userId) {
      loadUserDataSummary();
    }
  }, [userId]);

  useEffect(() => {
    if (selectedCompetition) {
      loadSensorData();
    }
  }, [selectedCompetition]);

  const loadUserDataSummary = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`http://localhost:8000/admin/users/${userId}/data-summary`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('API Error Response:', errorText);
        throw new Error(`ユーザーデータ取得に失敗しました (${response.status}): ${errorText}`);
      }
      
      const data = await response.json();
      console.log('Full API Response:', JSON.stringify(data, null, 2)); // 完全なAPIレスポンスをログ出力
      
      // 🛡️ データの存在チェック
      if (!data || typeof data !== 'object') {
        throw new Error('無効なデータ形式です');
      }
      
      console.log('user_info:', data.user_info); // user_infoを個別にログ出力
      
      setUserDataSummary(data);
      
      // デフォルトで最初の大会を選択
      if (data.competitions && Array.isArray(data.competitions) && data.competitions.length > 0) {
        setSelectedCompetition(data.competitions[0].competition_id);
      }
    } catch (error) {
      console.error('Failed to load user data summary:', error);
      setError(`ユーザー情報の読み込みに失敗しました: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const loadSensorData = async () => {
    if (!selectedCompetition) return;
    
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(
        `http://localhost:8000/admin/users/${userId}/sensor-data?competition_id=${selectedCompetition}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) throw new Error('センサーデータ取得に失敗しました');
      
      const data = await response.json();
      setSensorData(data.sensor_data || []);
    } catch (error) {
      console.error('Failed to load sensor data:', error);
    }
  };

  // 🔄 実際のAPIレスポンスに合わせて変数を修正
  console.log('UserDetail - userId:', userId);
  console.log('UserDetail - userDataSummary:', userDataSummary);

  if (isLoading) {
    return (
      <Layout>
        <div className="text-center py-8">
          <LoadingSpinner size="lg" text="読み込み中..." />
        </div>
      </Layout>
    );
  }

  if (error || !userDataSummary) {
    return (
      <Layout>
        <div className="text-center py-8">
          <div className="text-red-600 mb-4">{error || 'ユーザーが見つかりません'}</div>
          <Button onClick={() => navigate('/admin/users')}>
            ユーザー一覧に戻る
          </Button>
        </div>
      </Layout>
    );
  }

  // 🛡️ 安全なデータアクセスのためのnullチェック
  if (!userDataSummary) {
    return (
      <Layout>
        <div className="text-center py-8">
          <div className="text-red-600 mb-4">データの読み込みに失敗しました</div>
          <Button onClick={() => navigate('/admin/users')}>
            ユーザー一覧に戻る
          </Button>
        </div>
      </Layout>
    );
  }

  // 🛡️ user_idの存在確認
  if (!userDataSummary?.user_id) {
    return (
      <Layout>
        <div className="text-center py-8">
          <div className="text-red-600 mb-4">ユーザーIDが見つかりません</div>
          <Button onClick={() => navigate('/admin/users')}>
            ユーザー一覧に戻る
          </Button>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-8">
        {/* ヘッダー */}
        <div className="bg-gradient-to-r from-green-600 to-green-700 rounded-lg p-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-white mb-2">
                {userDataSummary?.user_id || 'Unknown User'} さんのダッシュボード
              </h1>
              <p className="text-green-100">
                センサーデータと参加大会の詳細情報
              </p>
            </div>
            <Button
              onClick={() => navigate('/admin/users')}
              variant="outline"
              className="bg-white/10 border-white/20 text-white hover:bg-white/20"
            >
              ユーザー一覧に戻る
            </Button>
          </div>
        </div>

        {/* 上段: ユーザープロフィール */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">プロフィール</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <label className="text-sm font-medium text-gray-600">User ID</label>
              <p className="text-lg font-semibold text-gray-900">
                {userDataSummary?.user_id || 'N/A'}
              </p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-600">参加大会数</label>
              <p className="text-lg font-semibold text-gray-900">
                {userDataSummary?.total_competitions?.toLocaleString() || '0'}
              </p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-600">総データレコード数</label>
              <p className="text-lg font-semibold text-gray-900">
                {((userDataSummary?.skin_temperature_records || 0) + 
                  (userDataSummary?.core_temperature_records || 0) + 
                  (userDataSummary?.heart_rate_records || 0)).toLocaleString()}
              </p>
            </div>
          </div>
        </Card>

        {/* 下段: 大会選択とデータ表示 */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-gray-900">参加大会データ</h2>
            {userDataSummary?.competitions && userDataSummary.competitions.length > 0 && (
              <select
                value={selectedCompetition}
                onChange={(e) => setSelectedCompetition(e.target.value)}
                className="border border-gray-300 rounded-lg px-3 py-2 bg-white"
              >
                <option value="">大会を選択してください</option>
                {userDataSummary.competitions.map((competition) => (
                  <option key={competition.competition_id} value={competition.competition_id}>
                    {competition?.name || 'Unknown Competition'} 
                    {competition?.date && ` (${new Date(competition.date).toLocaleDateString('ja-JP')})`}
                  </option>
                ))}
              </select>
            )}
          </div>

          {!userDataSummary?.competitions || userDataSummary.competitions.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              参加大会がありません
            </div>
          ) : !selectedCompetition ? (
            <div className="text-center py-8 text-gray-500">
              大会を選択してデータを表示してください
            </div>
          ) : (
            <div className="space-y-6">
              {/* データ統計 */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-blue-50 p-4 rounded-lg text-center">
                  <div className="text-2xl font-bold text-blue-600">
                    {userDataSummary?.skin_temperature_records?.toLocaleString() || '0'}
                  </div>
                  <div className="text-sm text-blue-600">体表温データ</div>
                </div>
                <div className="bg-red-50 p-4 rounded-lg text-center">
                  <div className="text-2xl font-bold text-red-600">
                    {userDataSummary?.core_temperature_records?.toLocaleString() || '0'}
                  </div>
                  <div className="text-sm text-red-600">カプセル体温データ</div>
                </div>
                <div className="bg-green-50 p-4 rounded-lg text-center">
                  <div className="text-2xl font-bold text-green-600">
                    {userDataSummary?.heart_rate_records?.toLocaleString() || '0'}
                  </div>
                  <div className="text-sm text-green-600">心拍データ</div>
                </div>
              </div>

              {/* センサーデータテーブル表示 */}
              {sensorData.length > 0 ? (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    センサーデータ詳細
                  </h3>
                  <div className="overflow-x-auto">
                    <table className="min-w-full bg-white border border-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">
                            センサー種別
                          </th>
                          <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">
                            センサーID
                          </th>
                          <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">
                            レコード数
                          </th>
                          <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">
                            最新記録時刻
                          </th>
                          <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">
                            データ範囲
                          </th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-200">
                        {sensorData.map((data, index) => (
                          <tr key={index} className="hover:bg-gray-50">
                            <td className="px-4 py-3 text-sm text-gray-900">
                              {data?.sensor_type || 'N/A'}
                            </td>
                            <td className="px-4 py-3 text-sm text-gray-900">
                              {data?.sensor_id || 'N/A'}
                            </td>
                            <td className="px-4 py-3 text-sm text-gray-900">
                              {data?.record_count?.toLocaleString() || '0'}
                            </td>
                            <td className="px-4 py-3 text-sm text-gray-900">
                              {data?.latest_record ? new Date(data.latest_record).toLocaleString('ja-JP') : 'N/A'}
                            </td>
                            <td className="px-4 py-3 text-sm text-gray-900">
                              {data?.data_range || 'N/A'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  選択した大会のセンサーデータがありません
                </div>
              )}
            </div>
          )}
        </Card>
      </div>
    </Layout>
  );
};