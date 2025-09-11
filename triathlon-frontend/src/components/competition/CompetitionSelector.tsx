import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

interface Competition {
  id: number;
  competition_id: string;
  name: string;
  date: string | null;
  location: string | null;
  description: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string | null;
  participant_count?: number;
  sensor_data_count?: number;
}

interface CompetitionSelectorProps {
  selectedCompetitionId: string | null;
  onCompetitionSelect: (competitionId: string | null) => void;
  showAllOption?: boolean;
}

// 一般ユーザー用大会選択コンポーネント
export const CompetitionSelector: React.FC<CompetitionSelectorProps> = ({
  selectedCompetitionId,
  onCompetitionSelect,
  showAllOption = true
}) => {
  const [competitions, setCompetitions] = useState<Competition[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchMyCompetitions();
  }, []);

  const fetchMyCompetitions = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      // me/ エンドポイントを使用（一般ユーザー本人のデータ）
      const response = await fetch('/me/competitions', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch competitions');
      }

      const data = await response.json();
      setCompetitions(data);
      
    } catch (err) {
      console.error('Error fetching competitions:', err);
      setError('大会データの取得に失敗しました');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Card className="p-6">
        <div className="flex items-center justify-center">
          <LoadingSpinner size="sm" />
          <span className="ml-2 text-gray-600">大会データを読み込み中...</span>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="p-6 border-red-200 bg-red-50">
        <div className="text-red-700 text-center">
          <p className="font-medium">エラーが発生しました</p>
          <p className="text-sm mt-1">{error}</p>
          <Button 
            onClick={fetchMyCompetitions}
            className="mt-3 text-sm"
            variant="outline"
          >
            再試行
          </Button>
        </div>
      </Card>
    );
  }

  return (
    <Card className="overflow-hidden">
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 px-6 py-4">
        <h3 className="text-lg font-semibold text-white flex items-center">
          <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          大会選択
        </h3>
        <p className="text-blue-100 text-sm mt-1">
          参加した大会からデータを表示する大会を選択してください
        </p>
      </div>

      <div className="p-6">
        <div className="space-y-3">
          {showAllOption && (
            <div
              className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                selectedCompetitionId === null
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
              onClick={() => onCompetitionSelect(null)}
            >
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-medium text-gray-900">全大会のデータ</h4>
                  <p className="text-sm text-gray-600">すべての参加大会のデータを統合表示</p>
                </div>
                {selectedCompetitionId === null && (
                  <div className="w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center">
                    <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                )}
              </div>
            </div>
          )}

          {competitions.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <svg className="w-12 h-12 mx-auto mb-4 text-gray-300" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M4 4a2 2 0 012-2h8a2 2 0 012 2v12a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm3 1h6v4H7V5zm8 8v2h1v-2h-1zm-2-2H7v4h6v-4z" clipRule="evenodd" />
              </svg>
              <p className="text-lg font-medium">参加大会がありません</p>
              <p className="text-sm mt-1">まだ大会に参加していません</p>
            </div>
          ) : (
            competitions.map((competition) => (
              <div
                key={competition.id}
                className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                  selectedCompetitionId === competition.competition_id
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => onCompetitionSelect(competition.competition_id)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <h4 className="font-medium text-gray-900">{competition.name}</h4>
                    <div className="flex items-center gap-4 text-sm text-gray-600 mt-1">
                      {competition.date && (
                        <span className="flex items-center">
                          <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd" />
                          </svg>
                          {new Date(competition.date).toLocaleDateString('ja-JP')}
                        </span>
                      )}
                      {competition.location && (
                        <span className="flex items-center">
                          <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
                          </svg>
                          {competition.location}
                        </span>
                      )}
                    </div>
                  </div>
                  {selectedCompetitionId === competition.competition_id && (
                    <div className="w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center">
                      <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
        </div>

        <div className="mt-6 p-4 bg-gray-50 rounded-lg">
          <div className="text-sm text-gray-600">
            <span className="font-medium">選択状況: </span>
            {selectedCompetitionId 
              ? `選択中: ${competitions.find(c => c.competition_id === selectedCompetitionId)?.name || '不明な大会'}`
              : showAllOption 
                ? '選択中: 全大会のデータ'
                : '大会が選択されていません'
            }
          </div>
        </div>
      </div>
    </Card>
  );
};

// 管理者用大会選択コンポーネント
export const AdminCompetitionSelector: React.FC<CompetitionSelectorProps> = ({
  selectedCompetitionId,
  onCompetitionSelect,
  showAllOption = true
}) => {
  const [competitions, setCompetitions] = useState<Competition[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAllCompetitions();
  }, []);

  const fetchAllCompetitions = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      // admin/ エンドポイントを使用（管理者専用）
      const response = await fetch('/admin/competitions?include_inactive=true', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch competitions');
      }

      const data = await response.json();
      setCompetitions(data);
      
    } catch (err) {
      console.error('Error fetching competitions:', err);
      setError('大会データの取得に失敗しました');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Card className="p-6">
        <div className="flex items-center justify-center">
          <LoadingSpinner size="sm" />
          <span className="ml-2 text-gray-600">大会データを読み込み中...</span>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="p-6 border-red-200 bg-red-50">
        <div className="text-red-700 text-center">
          <p className="font-medium">エラーが発生しました</p>
          <p className="text-sm mt-1">{error}</p>
          <Button 
            onClick={fetchAllCompetitions}
            className="mt-3 text-sm"
            variant="outline"
          >
            再試行
          </Button>
        </div>
      </Card>
    );
  }

  return (
    <Card className="overflow-hidden">
      <div className="bg-gradient-to-r from-purple-600 to-purple-700 px-6 py-4">
        <h3 className="text-lg font-semibold text-white flex items-center">
          <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          大会選択（管理者）
        </h3>
        <p className="text-purple-100 text-sm mt-1">
          全大会からデータを表示する大会を選択してください
        </p>
      </div>

      <div className="p-6">
        <div className="space-y-3">
          {showAllOption && (
            <div
              className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                selectedCompetitionId === null
                  ? 'border-purple-500 bg-purple-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
              onClick={() => onCompetitionSelect(null)}
            >
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-medium text-gray-900">全大会のデータ</h4>
                  <p className="text-sm text-gray-600">すべての大会のデータを統合表示</p>
                </div>
                {selectedCompetitionId === null && (
                  <div className="w-5 h-5 bg-purple-500 rounded-full flex items-center justify-center">
                    <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                )}
              </div>
            </div>
          )}

          {competitions.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <svg className="w-12 h-12 mx-auto mb-4 text-gray-300" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M4 4a2 2 0 012-2h8a2 2 0 012 2v12a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm3 1h6v4H7V5zm8 8v2h1v-2h-1zm-2-2H7v4h6v-4z" clipRule="evenodd" />
              </svg>
              <p className="text-lg font-medium">大会がありません</p>
              <p className="text-sm mt-1">まだ大会が作成されていません</p>
            </div>
          ) : (
            competitions.map((competition) => (
              <div
                key={competition.id}
                className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                  selectedCompetitionId === competition.competition_id
                    ? 'border-purple-500 bg-purple-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => onCompetitionSelect(competition.competition_id)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h4 className="font-medium text-gray-900">{competition.name}</h4>
                      <span
                        className={`px-2 py-1 text-xs font-medium rounded-full ${
                          competition.is_active
                            ? 'bg-green-100 text-green-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {competition.is_active ? 'アクティブ' : '非アクティブ'}
                      </span>
                    </div>
                    <div className="flex items-center gap-4 text-sm text-gray-600">
                      {competition.date && (
                        <span className="flex items-center">
                          <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd" />
                          </svg>
                          {new Date(competition.date).toLocaleDateString('ja-JP')}
                        </span>
                      )}
                      {competition.location && (
                        <span className="flex items-center">
                          <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
                          </svg>
                          {competition.location}
                        </span>
                      )}
                      <span className="flex items-center">
                        <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                          <path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3z" />
                        </svg>
                        参加者: {competition.participant_count || 0}人
                      </span>
                    </div>
                  </div>
                  {selectedCompetitionId === competition.competition_id && (
                    <div className="w-5 h-5 bg-purple-500 rounded-full flex items-center justify-center">
                      <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
        </div>

        <div className="mt-6 p-4 bg-gray-50 rounded-lg">
          <div className="text-sm text-gray-600">
            <span className="font-medium">選択状況: </span>
            {selectedCompetitionId 
              ? `選択中: ${competitions.find(c => c.competition_id === selectedCompetitionId)?.name || '不明な大会'}`
              : showAllOption 
                ? '選択中: 全大会のデータ'
                : '大会が選択されていません'
            }
          </div>
        </div>
      </div>
    </Card>
  );
};