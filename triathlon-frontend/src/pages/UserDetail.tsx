// src/pages/UserDetail.tsx - エラー修正版

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Layout } from '@/components/layout/Layout';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { TriathlonFeedbackChart } from '@/components/charts/TriathlonFeedbackChart';
import { feedbackService } from '@/services/feedbackService';

// ✅ 型定義
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

interface Competition {
  id: string;
  name: string;
  date: string;
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
  const [competitions, setCompetitions] = useState<Competition[]>([]);  // ✅ 追加
  const [sensorData, setSensorData] = useState<SensorData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [viewMode, setViewMode] = useState<'summary' | 'chart'>('summary');  // ✅ 追加

  useEffect(() => {
    if (userId) {
      loadUserDataSummary();
      loadUserCompetitions();  // ✅ 追加
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
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/admin/users/${userId}/data-summary`, {
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

  // ✅ 追加：ユーザーの参加大会を取得
  const loadUserCompetitions = async () => {
    try {
      console.log('🔍 Loading competitions for user:', userId);
      const competitions = await feedbackService.getAdminUserCompetitions(userId!);
      console.log('📊 Fetched competitions:', competitions);
      
      setCompetitions(competitions);
      
      // デフォルトで最新の大会を選択
      if (competitions.length > 0) {
        const latestCompetition = competitions.reduce((latest: Competition, comp: Competition) => 
          new Date(comp.date) > new Date(latest.date) ? comp : latest
        );
        setSelectedCompetition(latestCompetition.id);
        console.log('🎯 Auto-selected competition:', latestCompetition);
      }
      
    } catch (error) {
      console.error('❌ Failed to load user competitions:', error);
      setError('参加大会の読み込みに失敗しました');
    }
  };

  const loadSensorData = async () => {
    if (!selectedCompetition) return;
    
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/admin/users/${userId}/feedback-data/${selectedCompetition}`,
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
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                {userDataSummary.user_info.full_name} さんのダッシュボード
              </h1>
              <p className="text-green-100">
                センサーデータと参加大会の詳細情報
              </p>
            </div>
            <div className="flex items-center gap-4">
              {/* ✅ 表示モード切り替えボタン */}
              <div className="flex items-center bg-white/10 rounded-lg p-1">
                <button
                  onClick={() => setViewMode('summary')}
                  className={`px-3 py-1 rounded text-sm transition-colors ${
                    viewMode === 'summary'
                      ? 'bg-white text-green-700 font-medium'
                      : 'text-white hover:bg-white/20'
                  }`}
                >
                  データ概要
                </button>
                <button
                  onClick={() => setViewMode('chart')}
                  className={`px-3 py-1 rounded text-sm transition-colors ${
                    viewMode === 'chart'
                      ? 'bg-white text-green-700 font-medium'
                      : 'text-white hover:bg-white/20'
                  }`}
                >
                  グラフ表示
                </button>
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
        </div>

        {/* データ概要モード */}
        {viewMode === 'summary' && (
          <>
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
          </>
        )}

        {/* グラフ表示モード */}
        {viewMode === 'chart' && (
          <>
            {/* 参加大会一覧 */}
            <Card className="p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                参加大会一覧
              </h2>
              <p className="text-sm text-gray-600 mb-4">
                大会を選択して詳細なフィードバックグラフを確認できます
              </p>
              
              {competitions.length === 0 ? (
                <p className="text-gray-500 text-center py-8">
                  参加大会がありません
                </p>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {competitions.map((competition) => (
                    <div
                      key={competition.id}
                      className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                        selectedCompetition === competition.id
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                      }`}
                      onClick={() => {
                        console.log('🎯 Competition selected:', competition);
                        setSelectedCompetition(competition.id);
                      }}
                    >
                      <h3 className="font-medium text-gray-900 mb-1">
                        {competition.name}
                      </h3>
                      <p className="text-sm text-gray-500 mb-1">
                        {new Date(competition.date).toLocaleDateString('ja-JP')}
                      </p>
                      {selectedCompetition === competition.id && (
                        <div className="mt-2">
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                            選択中
                          </span>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </Card>

            {/* フィードバックグラフ - 一般ユーザーと同じコンポーネント */}
            {competitions.length > 0 && (
              <Card className="p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">
                  {userDataSummary.user_info.full_name} さんのトライアスロン フィードバックグラフ
                </h2>
                <p className="text-sm text-gray-600 mb-6">
                  センサーデータと競技区間（Swim/Bike/Run）を時系列で確認できます。
                  時間範囲の調整やオフセット機能も利用可能です。
                </p>
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
                  <div className="flex items-start">
                    <svg className="h-5 w-5 text-yellow-600 mt-0.5 mr-2 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <div>
                      <h3 className="text-sm font-medium text-yellow-800">
                        管理者ビュー - 一般ユーザーと同じグラフ機能
                      </h3>
                      <p className="text-sm text-yellow-700 mt-1">
                        このグラフは一般ユーザーが自分のダッシュボードで見ているものと同じです。
                        時間範囲設定、オフセット調整、競技区間表示などすべての機能を利用できます。
                      </p>
                    </div>
                  </div>
                </div>
                <TriathlonFeedbackChart
                  userId={userId}
                  competitions={competitions}
                  competitionId={selectedCompetition}
                  height={600}
                  isAdminView={true}
                />
              </Card>
            )}
          </>
        )}

        {/* デバッグ情報（開発用） */}
        {process.env.NODE_ENV === 'development' && (
          <Card className="p-6 bg-gray-50">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">デバッグ情報</h3>
            <div className="space-y-2 text-xs">
              <div><strong>Current viewMode:</strong> {viewMode}</div>
              <div><strong>Competitions count:</strong> {competitions.length}</div>
              <div><strong>Selected competition:</strong> {selectedCompetition}</div>
              <div><strong>User ID:</strong> {userId}</div>
              <div><strong>API called:</strong> /admin/users/{userId}/competitions</div>
            </div>
            
            {/* 大会データの詳細 */}
            {competitions.length > 0 && (
              <div className="mt-4">
                <h4 className="font-medium text-gray-800 mb-2">取得された大会データ:</h4>
                <pre className="text-xs text-gray-600 bg-white p-3 rounded overflow-auto max-h-40">
                  {JSON.stringify(competitions, null, 2)}
                </pre>
              </div>
            )}
            
            {/* ユーザーデータ */}
            <div className="mt-4">
              <h4 className="font-medium text-gray-800 mb-2">ユーザーデータ:</h4>
              <pre className="text-xs text-gray-600 bg-white p-3 rounded overflow-auto max-h-60">
                {JSON.stringify(userDataSummary, null, 2)}
              </pre>
            </div>
          </Card>
        )}
      </div>
    </Layout>
  );
};