// UserDashboard.tsx - デバッグログ追加版

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
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
  const navigate = useNavigate();

  useEffect(() => {
    fetchUserDataSummary();
    fetchCompetitions();
  }, []);

  const fetchUserDataSummary = async () => {
    try {
      setIsLoading(true);
      setError('');
      
      const token = localStorage.getItem('access_token');
      
      const url = `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/me/data-summary`;
      
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        // console.error('❌ Response error:', errorText);
        throw new Error(`データ取得に失敗しました: ${response.status} - ${errorText}`);
      }

      const responseText = await response.text();
      
      let data;
      try {
        data = JSON.parse(responseText);
      } catch (parseError) {
        console.error('❌ JSON parse error:', parseError);
        console.error('❌ Response text:', responseText);
        throw new Error('Invalid JSON response');
      }
      
      
      // バックエンドのレスポンス形式に合わせて変換
      const transformedData = {
        user_info: {
          user_id: user?.username || 'N/A',
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
      const data = await feedbackService.getUserCompetitions();
      setCompetitions(data);
      
      if (data.length > 0 && !selectedCompetition) {
        const latest = data[0];
        // console.log('🎯 Auto-selecting competition:', latest);
        setSelectedCompetition(latest.id);
      }
    } catch (error: any) {
      console.error('❌ Failed to fetch competitions:', error);
      setError('大会一覧の取得に失敗しました');
    }
  };

  const handleRefresh = () => {
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
              {userDataSummary?.user_info.full_name}さんのダッシュボード
            </h1>
            <p className="text-gray-600 mt-1">
              センサーデータとパフォーマンス情報
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
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-gray-500">ユーザー名</p>
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
            <Button onClick={() => navigate('/user/change-credentials')} variant="outline">
              ログイン情報変更
            </Button>
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