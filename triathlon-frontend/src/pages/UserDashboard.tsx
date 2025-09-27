import React, { useState, useEffect } from 'react';
import { Layout } from '@/components/layout/Layout';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { useAuth } from '@/contexts/AuthContext';

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
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchUserDataSummary();
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
      setUserDataSummary(data);
      
      // デフォルトで最初の大会を選択
      if (data.competitions && data.competitions.length > 0) {
        setSelectedCompetition(data.competitions[0].competition_id);
      }
    } catch (error) {
      console.error('Failed to fetch user data summary:', error);
      setError('データの取得に失敗しました');
    } finally {
      setIsLoading(false);
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
            {userDataSummary.user_info.full_name} さんのダッシュボード
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

        {/* センサーデータ統計 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          <Card className="p-4 bg-blue-50 border-blue-200">
            <div className="text-center">
              <p className="text-sm font-medium text-blue-700 mb-1">体表温データ</p>
              <p className="text-2xl font-bold text-blue-900">
                {userDataSummary.sensor_data_summary.skin_temperature.toLocaleString()}
              </p>
              <p className="text-xs text-blue-600 mt-1">件</p>
            </div>
          </Card>

          <Card className="p-4 bg-red-50 border-red-200">
            <div className="text-center">
              <p className="text-sm font-medium text-red-700 mb-1">カプセル体温</p>
              <p className="text-2xl font-bold text-red-900">
                {userDataSummary.sensor_data_summary.core_temperature.toLocaleString()}
              </p>
              <p className="text-xs text-red-600 mt-1">件</p>
            </div>
          </Card>

          <Card className="p-4 bg-green-50 border-green-200">
            <div className="text-center">
              <p className="text-sm font-medium text-green-700 mb-1">心拍データ</p>
              <p className="text-2xl font-bold text-green-900">
                {userDataSummary.sensor_data_summary.heart_rate.toLocaleString()}
              </p>
              <p className="text-xs text-green-600 mt-1">件</p>
            </div>
          </Card>

          <Card className="p-4 bg-purple-50 border-purple-200">
            <div className="text-center">
              <p className="text-sm font-medium text-purple-700 mb-1">マッピング数</p>
              <p className="text-2xl font-bold text-purple-900">
                {userDataSummary.mappings_count.toLocaleString()}
              </p>
              <p className="text-xs text-purple-600 mt-1">個</p>
            </div>
          </Card>

          <Card className="p-4 bg-yellow-50 border-yellow-200">
            <div className="text-center">
              <p className="text-sm font-medium text-yellow-700 mb-1">参加大会数</p>
              <p className="text-2xl font-bold text-yellow-900">
                {userDataSummary.competitions_participated.toLocaleString()}
              </p>
              <p className="text-xs text-yellow-600 mt-1">大会</p>
            </div>
          </Card>
        </div>

        {/* 参加大会一覧 */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">参加大会</h2>
          
          {userDataSummary.competitions.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <div className="mb-4">
                <svg className="h-12 w-12 text-gray-400 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
                </svg>
              </div>
              <p className="text-lg font-medium">参加大会がありません</p>
              <p className="text-sm mt-1">
                大会に参加してセンサーデータが登録されると、ここに表示されます。
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {/* 大会選択 */}
              <div className="flex items-center gap-4">
                <label className="text-sm font-medium text-gray-700">表示する大会:</label>
                <select
                  value={selectedCompetition}
                  onChange={(e) => setSelectedCompetition(e.target.value)}
                  className="block w-auto rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                >
                  <option value="">-- 大会を選択 --</option>
                  {userDataSummary.competitions.map((comp) => (
                    <option key={comp.competition_id} value={comp.competition_id}>
                      {comp.name} ({new Date(comp.date).toLocaleDateString('ja-JP')})
                    </option>
                  ))}
                </select>
              </div>

              {/* 大会一覧表示 */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {userDataSummary.competitions.map((competition) => (
                  <div
                    key={competition.competition_id}
                    className={`border rounded-lg p-4 transition-colors ${
                      selectedCompetition === competition.competition_id
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <h3 className="font-semibold text-gray-900 mb-2">
                      {competition.name}
                    </h3>
                    <div className="text-sm text-gray-600 space-y-1">
                      <p>開催日: {new Date(competition.date).toLocaleDateString('ja-JP')}</p>
                      {competition.bib_number && (
                        <p>ゼッケン番号: {competition.bib_number}</p>
                      )}
                      <p>大会ID: {competition.competition_id}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </Card>

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
                センサーマッピングが設定され、データがアップロードされると、ここに詳細情報が表示されます。
              </p>
            </div>
          ) : !selectedCompetition ? (
            <div className="text-center py-8 text-gray-500">
              <p className="text-lg font-medium">大会を選択してください</p>
              <p className="text-sm mt-1">
                上記で大会を選択すると、その大会でのセンサーデータの詳細を確認できます。
              </p>
            </div>
          ) : (
            <div className="text-center py-8 text-blue-600">
              <div className="mb-4">
                <svg className="h-12 w-12 text-blue-400 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <p className="text-lg font-medium">センサーデータ詳細表示</p>
              <p className="text-sm mt-1">
                総レコード数: {userDataSummary.total_sensor_records.toLocaleString()} 件
              </p>
              <p className="text-sm mt-1 text-gray-500">
                詳細なデータ表示・グラフ機能は今後実装予定です
              </p>
            </div>
          )}
        </Card>

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