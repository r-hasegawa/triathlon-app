import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Layout } from '@/components/layout/Layout';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

interface UserDetail {
  user_id: string;
  name: string;
  email: string;
  created_at: string;
}

interface Competition {
  competition_id: string;
  name: string;
  date: string;
  status: string;
}

interface UserData {
  skin_temperature_records: number;
  core_temperature_records: number;
  heart_rate_records: number;
  competitions: Competition[];
  total_competitions: number;
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
  
  const [user, setUser] = useState<UserDetail | null>(null);
  const [userData, setUserData] = useState<UserData | null>(null);
  const [selectedCompetition, setSelectedCompetition] = useState<string>('');
  const [sensorData, setSensorData] = useState<SensorData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (userId) {
      loadUserDetail();
      loadUserData();
    }
  }, [userId]);

  useEffect(() => {
    if (selectedCompetition) {
      loadSensorData();
    }
  }, [selectedCompetition]);

  const loadUserDetail = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`http://localhost:8000/admin/users/${userId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) throw new Error('ユーザー詳細取得に失敗しました');
      
      const data = await response.json();
      setUser(data);
    } catch (error) {
      console.error('Failed to load user detail:', error);
      setError('ユーザー情報の読み込みに失敗しました');
    }
  };

  const loadUserData = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`http://localhost:8000/admin/users/${userId}/data-summary`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) throw new Error('ユーザーデータ取得に失敗しました');
      
      const data = await response.json();
      setUserData(data);
      
      // デフォルトで最新の大会を選択
      if (data.competitions.length > 0) {
        setSelectedCompetition(data.competitions[0].competition_id);
      }
    } catch (error) {
      console.error('Failed to load user data:', error);
      setError('ユーザーデータの読み込みに失敗しました');
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

  if (isLoading) {
    return (
      <Layout>
        <div className="text-center py-8">
          <LoadingSpinner size="lg" text="読み込み中..." />
        </div>
      </Layout>
    );
  }

  if (error || !user) {
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

  return (
    <Layout>
      <div className="space-y-8">
        {/* ヘッダー */}
        <div className="bg-gradient-to-r from-green-600 to-green-700 rounded-lg p-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-white mb-2">
                {user.name} さんのダッシュボード
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
              <label className="text-sm font-medium text-gray-600">氏名</label>
              <p className="text-lg font-semibold text-gray-900">{user.name}</p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-600">メールアドレス</label>
              <p className="text-lg font-semibold text-gray-900">{user.email}</p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-600">User ID</label>
              <p className="text-lg font-semibold text-gray-900">{user.user_id}</p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-600">アカウント作成日</label>
              <p className="text-lg font-semibold text-gray-900">
                {new Date(user.created_at).toLocaleDateString('ja-JP')}
              </p>
            </div>
            {userData && (
              <>
                <div>
                  <label className="text-sm font-medium text-gray-600">参加大会数</label>
                  <p className="text-lg font-semibold text-gray-900">{userData.total_competitions}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-600">総データレコード数</label>
                  <p className="text-lg font-semibold text-gray-900">
                    {(userData.skin_temperature_records + 
                      userData.core_temperature_records + 
                      userData.heart_rate_records).toLocaleString()}
                  </p>
                </div>
              </>
            )}
          </div>
        </Card>

        {/* 下段: 大会選択とデータ表示 */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-gray-900">参加大会データ</h2>
            {userData && userData.competitions.length > 0 && (
              <select
                value={selectedCompetition}
                onChange={(e) => setSelectedCompetition(e.target.value)}
                className="border border-gray-300 rounded-lg px-3 py-2 bg-white"
              >
                <option value="">大会を選択してください</option>
                {userData.competitions.map((competition) => (
                  <option key={competition.competition_id} value={competition.competition_id}>
                    {competition.name} ({new Date(competition.date).toLocaleDateString('ja-JP')})
                  </option>
                ))}
              </select>
            )}
          </div>

          {!userData || userData.competitions.length === 0 ? (
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
                    {userData.skin_temperature_records.toLocaleString()}
                  </div>
                  <div className="text-sm text-blue-600">体表温データ</div>
                </div>
                <div className="bg-red-50 p-4 rounded-lg text-center">
                  <div className="text-2xl font-bold text-red-600">
                    {userData.core_temperature_records.toLocaleString()}
                  </div>
                  <div className="text-sm text-red-600">カプセル体温データ</div>
                </div>
                <div className="bg-green-50 p-4 rounded-lg text-center">
                  <div className="text-2xl font-bold text-green-600">
                    {userData.heart_rate_records.toLocaleString()}
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
                        {sensorData.map((sensor, index) => (
                          <tr key={index} className="hover:bg-gray-50">
                            <td className="px-4 py-3 text-sm text-gray-900">
                              {sensor.sensor_type}
                            </td>
                            <td className="px-4 py-3 text-sm font-mono text-gray-900">
                              {sensor.sensor_id}
                            </td>
                            <td className="px-4 py-3 text-sm text-gray-900">
                              {sensor.record_count.toLocaleString()}
                            </td>
                            <td className="px-4 py-3 text-sm text-gray-900">
                              {new Date(sensor.latest_record).toLocaleString('ja-JP')}
                            </td>
                            <td className="px-4 py-3 text-sm text-gray-900">
                              {sensor.data_range}
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

              {/* 将来の拡張: グラフ表示予定エリア */}
              <Card className="p-6 bg-gray-50 border-dashed border-2 border-gray-300">
                <div className="text-center py-8">
                  <div className="text-gray-400 mb-2">
                    <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-medium text-gray-600 mb-2">
                    フィードバックグラフ（開発予定）
                  </h3>
                  <p className="text-sm text-gray-500">
                    時系列グラフ、競技区間表示、心拍・温度データの可視化機能を実装予定です
                  </p>
                </div>
              </Card>
            </div>
          )}
        </Card>
      </div>
    </Layout>
  );
};