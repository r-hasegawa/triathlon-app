// src/pages/UserDetail.tsx - 完全修正版

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Layout } from '@/components/layout/Layout';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

// 🔄 実際のAPIレスポンス構造に合わせて修正
interface UserDataSummary {
  user_info: {
    user_id: string;
    full_name: string;
    email: string;
  };
  sensor_data_summary: {
    skin_temperature: number;
    core_temperature: number;
    heart_rate: number;
  };
  total_sensor_records: number;
  mappings_count: number;
  competitions_participated: number;
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
      console.log('Full API Response:', JSON.stringify(data, null, 2));
      
      // 🛡️ データの存在チェック
      if (!data || typeof data !== 'object') {
        throw new Error('無効なデータ形式です');
      }
      
      console.log('user_info:', data.user_info);
      
      setUserDataSummary(data);
      
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

  // 🛡️ user_info の存在確認（修正）
  if (!userDataSummary?.user_info?.user_id) {
    return (
      <Layout>
        <div className="text-center py-8">
          <div className="text-red-600 mb-4">ユーザー情報が不完全です</div>
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
                {userDataSummary.user_info.full_name} さんのダッシュボード
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
                {userDataSummary.user_info.user_id}
              </p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-600">氏名</label>
              <p className="text-lg font-semibold text-gray-900">
                {userDataSummary.user_info.full_name}
              </p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-600">メールアドレス</label>
              <p className="text-lg font-semibold text-gray-900">
                {userDataSummary.user_info.email}
              </p>
            </div>
          </div>
        </Card>

        {/* データ統計サマリー */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          <Card className="p-4 bg-blue-50 border-blue-200">
            <div className="text-center">
              <p className="text-sm font-medium text-blue-700 mb-1">体表温データ</p>
              <p className="text-2xl font-bold text-blue-900">
                {userDataSummary.sensor_data_summary.skin_temperature.toLocaleString()}
              </p>
            </div>
          </Card>

          <Card className="p-4 bg-red-50 border-red-200">
            <div className="text-center">
              <p className="text-sm font-medium text-red-700 mb-1">カプセル体温</p>
              <p className="text-2xl font-bold text-red-900">
                {userDataSummary.sensor_data_summary.core_temperature.toLocaleString()}
              </p>
            </div>
          </Card>

          <Card className="p-4 bg-green-50 border-green-200">
            <div className="text-center">
              <p className="text-sm font-medium text-green-700 mb-1">心拍データ</p>
              <p className="text-2xl font-bold text-green-900">
                {userDataSummary.sensor_data_summary.heart_rate.toLocaleString()}
              </p>
            </div>
          </Card>

          <Card className="p-4 bg-purple-50 border-purple-200">
            <div className="text-center">
              <p className="text-sm font-medium text-purple-700 mb-1">マッピング数</p>
              <p className="text-2xl font-bold text-purple-900">
                {userDataSummary.mappings_count.toLocaleString()}
              </p>
            </div>
          </Card>

          <Card className="p-4 bg-yellow-50 border-yellow-200">
            <div className="text-center">
              <p className="text-sm font-medium text-yellow-700 mb-1">参加大会数</p>
              <p className="text-2xl font-bold text-yellow-900">
                {userDataSummary.competitions_participated.toLocaleString()}
              </p>
            </div>
          </Card>
        </div>

        {/* データ詳細表示エリア */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">センサーデータ詳細</h2>
          
          {userDataSummary.total_sensor_records === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <div className="mb-4">
                <svg className="h-12 w-12 text-gray-400 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <p className="text-lg font-medium">センサーデータがありません</p>
              <p className="text-sm mt-1">
                このユーザーには現在登録されているセンサーデータがありません。
              </p>
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <p>総レコード数: {userDataSummary.total_sensor_records.toLocaleString()} 件</p>
              <p className="text-sm mt-1">
                センサーデータの詳細表示機能は今後実装予定です。
              </p>
            </div>
          )}
        </Card>

        {/* グラフエリア */}
        {viewMode === 'chart' && (
          <Card className="p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-gray-900">
                {user?.full_name || user?.username || 'ユーザー'} のフィードバックデータ
              </h2>
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-500">大会:</span>
                <select
                  value={selectedCompetition}
                  onChange={(e) => setSelectedCompetition(e.target.value)}
                  className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">大会を選択</option>
                  {competitions.map((comp) => (
                    <option key={comp.id} value={comp.id}>
                      {comp.name} ({new Date(comp.date).toLocaleDateString('ja-JP')})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {!selectedCompetition ? (
              <div className="text-center py-12 text-gray-500">
                <div className="mb-4">
                  <svg className="h-16 w-16 text-gray-300 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  大会を選択してください
                </h3>
                <p className="text-sm">
                  大会を選択すると、該当大会でのセンサーデータと競技区間が表示されます。
                </p>
              </div>
            ) : competitions.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <div className="mb-4">
                  <svg className="h-16 w-16 text-gray-300 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  参加大会データがありません
                </h3>
                <p className="text-sm">
                  このユーザーの大会参加データまたはセンサーデータが登録されていません。
                </p>
              </div>
            ) : (
              <TriathlonFeedbackChart
                userId={userId}
                competitions={competitions}
                competitionId={selectedCompetition}
                height={600}
                isAdminView={true}  // 追加：管理者ビュー用
              />
            )}
          </Card>
        )}

        {/* デバッグ情報（開発用） */}
        {process.env.NODE_ENV === 'development' && (
          <Card className="p-6 bg-gray-50">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">デバッグ情報</h3>
            <pre className="text-xs text-gray-600 bg-white p-4 rounded overflow-auto">
              {JSON.stringify(userDataSummary, null, 2)}
            </pre>
          </Card>
        )}
      </div>
    </Layout>
  );
};