import React, { useState, useEffect } from 'react';
import { Layout } from '@/components/layout/Layout';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { useAuth } from '@/contexts/AuthContext';
import { TriathlonFeedbackChart } from '@/components/charts/TriathlonFeedbackChart';
import { feedbackService, type CompetitionRace } from '@/services/feedbackService';

// 一般ユーザー向けデータサマリーの型定義
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
  competitions: Array<{
    competition_id: string;
    name: string;
    date: string;
    bib_number?: string;
  }>;
}

export const UserDashboard: React.FC = () => {
  const { user } = useAuth();
  const [userDataSummary, setUserDataSummary] = useState<UserDataSummary | null>(null);
  const [selectedCompetition, setSelectedCompetition] = useState<string>('');
  const [competitions, setCompetitions] = useState<CompetitionRace[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchUserDataSummary();
    fetchCompetitions();
  }, []);

  const fetchUserDataSummary = async () => {
    try {
      setIsLoading(true);
      setError('');
      
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:8000/me/data-summary', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`データ取得に失敗しました: ${response.status}`);
      }

      const data = await response.json();
      console.log('User data summary:', data);
      
      // バックエンドのレスポンス形式に合わせて変換
      const transformedData = {
        user_info: {
          user_id: user?.user_id || 'N/A',
          full_name: user?.full_name || user?.username || 'ユーザー',
          email: user?.email || 'N/A'
        },
        sensor_data_summary: {
          skin_temperature: 0,
          core_temperature: 0,
          heart_rate: 0
        },
        total_sensor_records: data.total_sensor_records || 0,
        mappings_count: 0,
        competitions_participated: data.competitions_participated || 0,
        competitions: []
      };
      
      setUserDataSummary(transformedData);
      
    } catch (error) {
      console.error('Failed to fetch user data summary:', error);
      setError('データの取得に失敗しました');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchCompetitions = async () => {
    try {
      const data = await feedbackService.getUserCompetitions();
      setCompetitions(data);
      
      // デフォルトで最初の大会を選択
      if (data && data.length > 0) {
        setSelectedCompetition(data[0].id);
      }
    } catch (error) {
      console.error('Failed to fetch competitions:', error);
    }
  };

  if (isLoading) {
    return (
      <Layout>
        <div className="flex justify-center items-center py-12">
          <LoadingSpinner size="lg" text="ダッシュボードを読み込んでいます..." />
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
            <Button onClick={fetchUserDataSummary} className="mt-3">
              再読み込み
            </Button>
          </div>
        </Card>
      </Layout>
    );
  }

  // データが取得できていない場合
  if (!userDataSummary) {
    return (
      <Layout>
        <Card className="p-6 border-yellow-200 bg-yellow-50">
          <div className="text-yellow-700 text-center">
            <p className="font-medium">データが見つかりません</p>
            <p className="text-sm mt-1">センサーデータやマッピング情報が登録されていない可能性があります</p>
            <Button onClick={fetchUserDataSummary} className="mt-3">
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
        {/* ヘッダー */}
        <div style={{
          background: 'linear-gradient(to right, #059669, #047857)',
          borderRadius: '8px',
          padding: '32px',
          color: 'white',
          boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)'
        }}>
          <h1 style={{
            fontSize: '1.875rem',
            fontWeight: 'bold',
            color: 'white',
            marginBottom: '8px',
            margin: 0
          }}>
            {userDataSummary?.user_info?.full_name || 'ユーザー'} さんのダッシュボード
          </h1>
          <p style={{
            color: 'rgba(255, 255, 255, 0.9)',
            margin: 0
          }}>
            あなたのセンサーデータと参加大会の情報
          </p>
        </div>

        {/* プロフィール情報 */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">プロフィール情報</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <label className="text-sm font-medium text-gray-600">User ID</label>
              <p className="text-lg font-semibold text-gray-900">
                {userDataSummary?.user_info?.user_id || '取得中...'}
              </p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-600">氏名</label>
              <p className="text-lg font-semibold text-gray-900">
                {userDataSummary?.user_info?.full_name || '取得中...'}
              </p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-600">メールアドレス</label>
              <p className="text-lg font-semibold text-gray-900">
                {userDataSummary?.user_info?.email || '取得中...'}
              </p>
            </div>
          </div>
        </Card>

        {/* センサーデータ統計 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          <Card className="p-4 bg-blue-50 border-blue-200">
            <div className="text-center">
              <p className="text-sm font-medium text-blue-700 mb-1">体表温データ</p>
              <p className="text-2xl font-bold text-blue-900">
                {userDataSummary?.sensor_data_summary?.skin_temperature?.toLocaleString() || '0'}
              </p>
              <p className="text-xs text-blue-600 mt-1">件</p>
            </div>
          </Card>

          <Card className="p-4 bg-red-50 border-red-200">
            <div className="text-center">
              <p className="text-sm font-medium text-red-700 mb-1">カプセル体温</p>
              <p className="text-2xl font-bold text-red-900">
                {userDataSummary?.sensor_data_summary?.core_temperature?.toLocaleString() || '0'}
              </p>
              <p className="text-xs text-red-600 mt-1">件</p>
            </div>
          </Card>

          <Card className="p-4 bg-green-50 border-green-200">
            <div className="text-center">
              <p className="text-sm font-medium text-green-700 mb-1">心拍データ</p>
              <p className="text-2xl font-bold text-green-900">
                {userDataSummary?.sensor_data_summary?.heart_rate?.toLocaleString() || '0'}
              </p>
              <p className="text-xs text-green-600 mt-1">件</p>
            </div>
          </Card>

          <Card className="p-4 bg-purple-50 border-purple-200">
            <div className="text-center">
              <p className="text-sm font-medium text-purple-700 mb-1">マッピング数</p>
              <p className="text-2xl font-bold text-purple-900">
                {userDataSummary?.mappings_count?.toLocaleString() || '0'}
              </p>
              <p className="text-xs text-purple-600 mt-1">個</p>
            </div>
          </Card>

          <Card className="p-4 bg-yellow-50 border-yellow-200">
            <div className="text-center">
              <p className="text-sm font-medium text-yellow-700 mb-1">参加大会数</p>
              <p className="text-2xl font-bold text-yellow-900">
                {userDataSummary?.competitions_participated?.toLocaleString() || '0'}
              </p>
              <p className="text-xs text-yellow-600 mt-1">大会</p>
            </div>
          </Card>
        </div>

        {/* 参加大会一覧 */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">参加大会</h2>
          
          {!competitions || competitions.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <div className="mb-4">
                <svg className="h-16 w-16 text-gray-300 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                参加大会がありません
              </h3>
              <p className="text-sm">
                管理者によって大会への参加登録が行われると、ここに表示されます。
              </p>
            </div>
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
                  onClick={() => setSelectedCompetition(competition.id)}
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

        {/* フィードバックグラフ */}
        {competitions.length > 0 && (
          <Card className="p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              トライアスロン フィードバックグラフ
            </h2>
            <p className="text-sm text-gray-600 mb-6">
              センサーデータと競技区間（Swim/Bike/Run）を時系列で確認できます
            </p>
            <TriathlonFeedbackChart
              competitions={competitions}
              competitionId={selectedCompetition}
              height={500}
            />
          </Card>
        )}

        {/* デバッグ情報（開発環境のみ） */}
        {process.env.NODE_ENV === 'development' && (
          <Card className="p-6 bg-gray-50">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">デバッグ情報</h3>
            <details className="text-sm">
              <summary className="cursor-pointer font-medium text-gray-700 mb-2">
                API レスポンスデータ（クリックで展開）
              </summary>
              <pre className="text-xs text-gray-600 bg-white p-4 rounded overflow-auto max-h-64">
                {JSON.stringify(userDataSummary, null, 2)}
              </pre>
            </details>
          </Card>
        )}
      </div>
    </Layout>
  );
};