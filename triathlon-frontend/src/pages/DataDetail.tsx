// src/pages/DataDetail.tsx

import React, { useState, useEffect } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { Layout } from '@/components/layout/Layout';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorMessage } from '@/components/ui/ErrorMessage';
import { TriathlonFeedbackChart } from '@/components/charts/TriathlonFeedbackChart';
import { SensorDataTable } from '@/components/data/SensorDataTable';
import { DataFilters } from '@/components/data/DataFilters';
import { useDataDetail } from '@/hooks/useDataDetail';
import { feedbackService, type CompetitionRace } from '@/services/feedbackService';
import { adminService } from '@/services/adminService';

interface User {
  user_id: string;
  username: string;
  full_name?: string;
  email?: string;
}

interface User {
  user_id: string;
  username: string;
  full_name?: string;
  email?: string;
}

export const DataDetail: React.FC = () => {
  const { userId } = useParams<{ userId: string }>();
  const [searchParams] = useSearchParams();
  const viewMode = searchParams.get('view') || 'table'; // 'table' | 'chart'

  const [user, setUser] = useState<User | null>(null);
  const [competitions, setCompetitions] = useState<CompetitionRace[]>([]);
  const [selectedCompetition, setSelectedCompetition] = useState<string>('');
  const [isUserLoading, setIsUserLoading] = useState(true);
  const [userError, setUserError] = useState('');

  const {
    data,
    sensors,
    totalCount,
    pageIndex,
    pageSize,
    filters,
    isLoading: isTableLoading,
    error: tableError,
    handleFiltersChange,
    handlePageChange,
    handlePageSizeChange,
    handleReset,
    refetch,
  } = useDataDetail();

  useEffect(() => {
    if (userId) {
      fetchUserAndCompetitions();
    }
  }, [userId]);

  const fetchUserAndCompetitions = async () => {
    if (!userId) return;

    try {
      setIsUserLoading(true);
      setUserError('');

      // ユーザー情報と参加大会一覧を取得
      const [userResponse, competitionsResponse] = await Promise.all([
        adminService.getUserById(userId),
        feedbackService.getAdminUserCompetitions(userId)
      ]);

      setUser(userResponse);
      setCompetitions(competitionsResponse);

      // デフォルトで最新の大会を選択
      if (competitionsResponse.length > 0) {
        const latestCompetition = competitionsResponse.reduce((latest, comp) => 
          new Date(comp.date) > new Date(latest.date) ? comp : latest
        );
        setSelectedCompetition(latestCompetition.id);
      }

    } catch (err: any) {
      console.error('User and competitions fetch error:', err);
      setUserError('ユーザー情報の取得に失敗しました');
    } finally {
      setIsUserLoading(false);
    }
  };

  const refreshAll = () => {
    fetchUserAndCompetitions();
    refetch();
  };

  if (isUserLoading) {
    return (
      <Layout>
        <div className="flex justify-center items-center min-h-96">
          <LoadingSpinner size="lg" text="ユーザーデータを読み込んでいます..." />
        </div>
      </Layout>
    );
  }

  if (userError) {
    return (
      <Layout>
        <div className="space-y-6">
          <ErrorMessage message={userError} onRetry={refreshAll} />
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6">
        {/* ヘッダー */}
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 mb-2">
                ユーザーデータ詳細
              </h1>
              {user && (
                <div className="text-sm text-gray-600">
                  <p><span className="font-medium">ユーザー:</span> {user.full_name || user.username}</p>
                  <p><span className="font-medium">ID:</span> {user.user_id}</p>
                  {user.email && (
                    <p><span className="font-medium">Email:</span> {user.email}</p>
                  )}
                </div>
              )}
            </div>
            
            <div className="flex gap-2">
              <Button
                variant={viewMode === 'chart' ? 'primary' : 'outline'}
                size="sm"
                onClick={() => {
                  const newParams = new URLSearchParams(searchParams);
                  newParams.set('view', 'chart');
                  window.history.replaceState({}, '', `?${newParams.toString()}`);
                  window.location.reload();
                }}
              >
                📊 グラフ表示
              </Button>
              <Button
                variant={viewMode === 'table' ? 'primary' : 'outline'}
                size="sm"
                onClick={() => {
                  const newParams = new URLSearchParams(searchParams);
                  newParams.set('view', 'table');
                  window.history.replaceState({}, '', `?${newParams.toString()}`);
                  window.location.reload();
                }}
              >
                📋 テーブル表示
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={refreshAll}
              >
                🔄 更新
              </Button>
            </div>
          </div>
        </Card>

        {/* フィードbackグラフ表示 */}
        {viewMode === 'chart' && (
          <Card className="p-6">
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-2">
                トライアスロン フィードバックグラフ
              </h2>
              <p className="text-sm text-gray-600">
                ユーザーのセンサーデータと競技区間（Swim/Bike/Run）を時系列で確認できます
              </p>
            </div>

            {competitions.length === 0 ? (
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
              />
            )}
          </Card>
        )}

        {/* 参加大会一覧（グラフ表示モード時） */}
        {viewMode === 'chart' && competitions.length > 0 && (
          <Card className="p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-6">参加大会一覧</h2>
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
                  <p className="text-sm text-gray-500">
                    {new Date(competition.date).toLocaleDateString('ja-JP', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric'
                    })}
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
          </Card>
        )}

        {/* テーブル表示モード */}
        {viewMode === 'table' && (
          <>
            {/* フィルター */}
            <Card className="p-6">
              <DataFilters
                sensors={sensors}
                filters={filters}
                onFiltersChange={handleFiltersChange}
                onReset={handleReset}
              />
            </Card>

            {/* データテーブル */}
            <Card className="p-6">
              {tableError && (
                <div className="mb-4">
                  <ErrorMessage message={tableError} onRetry={refetch} />
                </div>
              )}

              {isTableLoading && !data.length ? (
                <div className="flex justify-center py-12">
                  <LoadingSpinner size="lg" text="データを読み込んでいます..." />
                </div>
              ) : (
                <SensorDataTable
                  data={data}
                  isLoading={isTableLoading}
                  totalCount={totalCount}
                  pageIndex={pageIndex}
                  pageSize={pageSize}
                  onPageChange={handlePageChange}
                  onPageSizeChange={handlePageSizeChange}
                />
              )}
            </Card>
          </>
        )}
      </div>
    </Layout>
  );
};