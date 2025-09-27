// UserDashboard.tsx - デバッグログ追加版

import React, { useState, useEffect } from 'react';
import { Layout } from '@/components/layout/Layout';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { useAuth } from '@/contexts/AuthContext';
import { TriathlonFeedbackChart } from '@/components/charts/TriathlonFeedbackChart';
import { feedbackService, type CompetitionRace } from '@/services/feedbackService';

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
    console.log('🔄 UserDashboard useEffect triggered');
    fetchUserDataSummary();
    fetchCompetitions();
  }, []);

  const fetchUserDataSummary = async () => {
    try {
      console.log('📊 Fetching user data summary...');
      setIsLoading(true);
      setError('');
      
      const token = localStorage.getItem('access_token');
      console.log('🔑 Token exists:', !!token);
      console.log('🔑 Token preview:', token?.substring(0, 20) + '...');
      
      const url = 'http://localhost:8000/me/data-summary';
      console.log('🌐 Requesting URL:', url);
      
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      console.log('📨 Response status:', response.status);
      console.log('📨 Response headers:', Object.fromEntries(response.headers.entries()));
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ Response error:', errorText);
        throw new Error(`データ取得に失敗しました: ${response.status} - ${errorText}`);
      }

      const responseText = await response.text();
      console.log('📨 Raw response:', responseText);
      
      let data;
      try {
        data = JSON.parse(responseText);
        console.log('✅ Parsed data:', data);
      } catch (parseError) {
        console.error('❌ JSON parse error:', parseError);
        console.error('❌ Response text:', responseText);
        throw new Error('Invalid JSON response');
      }
      
      // データ構造の詳細ログ
      console.log('🔍 Data structure analysis:');
      console.log('  - Type:', typeof data);
      console.log('  - Keys:', Object.keys(data || {}));
      console.log('  - total_sensor_records:', data?.total_sensor_records);
      console.log('  - competitions_participated:', data?.competitions_participated);
      
      // バックエンドのレスポンス形式に合わせて変換
      const transformedData = {
        user_info: {
          user_id: user?.user_id || 'N/A',
          full_name: user?.full_name || user?.username || 'ユーザー',
          email: user?.email || 'N/A'
        },
        sensor_data_summary: {
          skin_temperature: data?.skin_temperature_count || 0,
          core_temperature: data?.core_temperature_count || 0,
          heart_rate: data?.heart_rate_count || 0
        },
        total_sensor_records: data?.total_sensor_records || 0,
        mappings_count: data?.mappings_count || 0,
        competitions_participated: data?.competitions_participated || 0,
        competitions: data?.competitions || []
      };
      
      console.log('🔄 Transformed data:', transformedData);
      setUserDataSummary(transformedData);
      
    } catch (error: any) {
      console.error('❌ Failed to fetch user data summary:', error);
      console.error('❌ Error stack:', error.stack);
      setError(`データの取得に失敗しました: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchCompetitions = async () => {
    try {
      console.log('🏆 Fetching competitions...');
      const data = await feedbackService.getUserCompetitions();
      console.log('✅ Competitions received:', data);
      setCompetitions(data);
      
      if (data.length > 0 && !selectedCompetition) {
        const latest = data[0];
        console.log('🎯 Auto-selecting competition:', latest);
        setSelectedCompetition(latest.id);
      }
    } catch (error: any) {
      console.error('❌ Failed to fetch competitions:', error);
      setError('大会一覧の取得に失敗しました');
    }
  };

  const handleRefresh = () => {
    console.log('🔄 Manual refresh triggered');
    fetchUserDataSummary();
    fetchCompetitions();
  };

  if (isLoading) {
    return (
      <Layout>
        <div className="flex justify-center items-center min-h-96">
          <LoadingSpinner size="lg" text="データを読み込んでいます..." />
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              マイダッシュボード
            </h1>
            <p className="text-gray-600 mt-1">
              あなたのセンサーデータとパフォーマンス情報
            </p>
          </div>
          <Button onClick={handleRefresh} variant="outline">
            🔄 更新
          </Button>
        </div>

        {/* エラー表示 */}
        {error && (
          <Card className="p-4 bg-red-50 border-red-200">
            <p className="text-red-600 font-medium">エラー:</p>
            <p className="text-red-600 text-sm">{error}</p>
          </Card>
        )}

        {/* ユーザー情報カード */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            ユーザー情報
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <p className="text-sm text-gray-500">ユーザーID</p>
              <p className="font-medium">{userDataSummary?.user_info.user_id}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">氏名</p>
              <p className="font-medium">{userDataSummary?.user_info.full_name}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">メールアドレス</p>
              <p className="font-medium">{userDataSummary?.user_info.email}</p>
            </div>
          </div>
        </Card>

        {/* データ統計カード */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            センサーデータ統計
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-600">
                {userDataSummary?.total_sensor_records || 0}
              </div>
              <div className="text-sm text-gray-500 mt-1">総センサーデータ</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-green-600">
                {userDataSummary?.sensor_data_summary.skin_temperature || 0}
              </div>
              <div className="text-sm text-gray-500 mt-1">体表温データ</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-red-600">
                {userDataSummary?.sensor_data_summary.core_temperature || 0}
              </div>
              <div className="text-sm text-gray-500 mt-1">カプセル体温</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-purple-600">
                {userDataSummary?.sensor_data_summary.heart_rate || 0}
              </div>
              <div className="text-sm text-gray-500 mt-1">心拍データ</div>
            </div>
          </div>
          
          {/* デバッグ情報表示 */}
          <details className="mt-4 p-4 bg-gray-50 rounded">
            <summary className="cursor-pointer text-sm font-medium text-gray-700">
              🐛 デバッグ情報を表示
            </summary>
            <div className="mt-2 text-xs">
              <p><strong>参加大会数:</strong> {userDataSummary?.competitions_participated}</p>
              <p><strong>マッピング数:</strong> {userDataSummary?.mappings_count}</p>
              <p><strong>取得した大会数:</strong> {competitions.length}</p>
              <p><strong>Raw API Response:</strong></p>
              <pre className="mt-2 p-2 bg-white rounded text-xs overflow-auto max-h-32">
                {JSON.stringify(userDataSummary, null, 2)}
              </pre>
            </div>
          </details>
        </Card>

        {/* 参加大会一覧 */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            参加大会一覧
          </h2>
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
              isAdminView={false}
            />
          </Card>
        )}
      </div>
    </Layout>
  );
};