/**
 * 大会選択コンポーネント
 * 被験者が自分の参加大会を選択するためのUI
 */

import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

// 型定義
interface Competition {
  id: number;
  competition_id: string;
  name: string;
  date: string | null;
  location: string | null;
  description: string | null;
  is_active: boolean;
  participant_count?: number;
  sensor_data_count?: number;
}

interface CompetitionSelectorProps {
  selectedCompetitionId?: string | null;
  onCompetitionSelect: (competitionId: string | null) => void;
  showAllOption?: boolean;  // "全大会" オプションを表示するか
}

export const CompetitionSelector: React.FC<CompetitionSelectorProps> = ({
  selectedCompetitionId,
  onCompetitionSelect,
  showAllOption = true
}) => {
  const [competitions, setCompetitions] = useState<Competition[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 自分の参加大会一覧を取得
  useEffect(() => {
    fetchMyCompetitions();
  }, []);

  const fetchMyCompetitions = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const response = await fetch('/api/competitions/my-competitions', {
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
      
      // 初回ロード時の大会選択（最新大会を自動選択）
      if (data.length > 0 && !selectedCompetitionId) {
        onCompetitionSelect(data[0].competition_id);
      }
      
    } catch (err) {
      console.error('Error fetching competitions:', err);
      setError('大会データの取得に失敗しました');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return '日程未定';
    const date = new Date(dateString);
    return date.toLocaleDateString('ja-JP', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      weekday: 'short'
    });
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

  if (competitions.length === 0) {
    return (
      <Card className="p-6 border-yellow-200 bg-yellow-50">
        <div className="text-yellow-700 text-center">
          <p className="font-medium">参加大会がありません</p>
          <p className="text-sm mt-1">まだトライアスロン大会に参加されていないか、データが準備中です。</p>
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
          データを表示する大会を選択してください
        </p>
      </div>

      <div className="p-6">
        <div className="space-y-3">
          {/* 全大会オプション */}
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
                  <h4 className="font-medium text-gray-900">
                    🏆 全大会のデータ
                  </h4>
                  <p className="text-sm text-gray-600 mt-1">
                    参加したすべての大会のデータを統合表示
                  </p>
                </div>
                <div className="text-right">
                  <div className="text-sm text-gray-500">
                    {competitions.length}大会
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 個別大会オプション */}
          {competitions.map((competition) => (
            <div
              key={competition.competition_id}
              className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                selectedCompetitionId === competition.competition_id
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
              onClick={() => onCompetitionSelect(competition.competition_id)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h4 className="font-medium text-gray-900">
                    {competition.name}
                  </h4>
                  <div className="mt-2 space-y-1 text-sm text-gray-600">
                    <div className="flex items-center">
                      <svg className="w-4 h-4 mr-1.5" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd" />
                      </svg>
                      {formatDate(competition.date)}
                    </div>
                  
                  {competition.description && (
                    <p className="text-sm text-gray-500 mt-2 line-clamp-2">
                      {competition.description}
                    </p>
                  )}
                </div>
                
                <div className="ml-4 text-right flex-shrink-0">
                  <div className="text-sm text-gray-500 space-y-1">
                    {competition.sensor_data_count && competition.sensor_data_count > 0 && (
                      <div className="flex items-center justify-end">
                        <svg className="w-4 h-4 mr-1 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                          <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <span>データあり</span>
                      </div>
                    )}
                    <div className="text-xs text-gray-400">
                      ID: {competition.competition_id.split('_').pop()}
                    </div>
                  </div>
                </div>
              </div>
              
              {/* 選択された大会の詳細情報 */}
              {selectedCompetitionId === competition.competition_id && (
                <div className="mt-4 pt-4 border-t border-blue-200">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500">センサデータ:</span>
                      <span className="ml-2 font-medium text-blue-600">
                        {competition.sensor_data_count?.toLocaleString() || '0'} 件
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500">参加者数:</span>
                      <span className="ml-2 font-medium text-blue-600">
                        {competition.participant_count || '0'} 名
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* 選択状況の表示 */}
        <div className="mt-6 p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center text-sm text-gray-600">
            <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
            <span>
              {selectedCompetitionId 
                ? `選択中: ${competitions.find(c => c.competition_id === selectedCompetitionId)?.name || '不明な大会'}`
                : showAllOption 
                  ? '選択中: 全大会のデータ'
                  : '大会が選択されていません'
              }
            </span>
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

  // 管理者は全大会一覧を取得
  useEffect(() => {
    fetchAllCompetitions();
  }, []);

  const fetchAllCompetitions = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      // ✅ 管理者用エンドポイントを使用
      const response = await fetch('/api/competitions/', {
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

  // 基本コンポーネントと同じUIを使用
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

  // 管理者向けのカスタマイズされたUI
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
          {/* 全大会オプション */}
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
                  <h4 className="font-medium text-gray-900">
                    🏆 全大会のデータ
                  </h4>
                  <p className="text-sm text-gray-600 mt-1">
                    すべての大会のデータを統合表示（管理者権限）
                  </p>
                </div>
                <div className="text-right">
                  <div className="text-sm text-gray-500">
                    {competitions.length}大会
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 個別大会オプション */}
          {competitions.map((competition) => (
            <div
              key={competition.competition_id}
              className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                selectedCompetitionId === competition.competition_id
                  ? 'border-purple-500 bg-purple-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
              onClick={() => onCompetitionSelect(competition.competition_id)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <h4 className="font-medium text-gray-900">
                      {competition.name}
                    </h4>
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
                  <div className="mt-2 space-y-1 text-sm text-gray-600">
                    <div className="flex items-center">
                      <svg className="w-4 h-4 mr-1.5" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd" />
                      </svg>
                      {formatDate(competition.date)}
                    </div>
                    {competition.location && (
                      <div className="flex items-center">
                        <svg className="w-4 h-4 mr-1.5" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
                        </svg>
                        {competition.location}
                      </div>
                    )}
                  </div>
                  
                  {competition.description && (
                    <p className="text-sm text-gray-500 mt-2 line-clamp-2">
                      {competition.description}
                    </p>
                  )}
                </div>
                
                <div className="ml-4 text-right flex-shrink-0">
                  <div className="text-sm text-gray-500 space-y-1">
                    {competition.sensor_data_count && competition.sensor_data_count > 0 && (
                      <div className="flex items-center justify-end">
                        <svg className="w-4 h-4 mr-1 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                          <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <span>データあり</span>
                      </div>
                    )}
                    <div className="text-xs text-gray-400">
                      ID: {competition.competition_id.split('_').pop()}
                    </div>
                  </div>
                </div>
              </div>
              
              {/* 選択された大会の詳細情報（管理者用追加情報） */}
              {selectedCompetitionId === competition.competition_id && (
                <div className="mt-4 pt-4 border-t border-purple-200">
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500">センサデータ:</span>
                      <span className="ml-2 font-medium text-purple-600">
                        {competition.sensor_data_count?.toLocaleString() || '0'} 件
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500">参加者数:</span>
                      <span className="ml-2 font-medium text-purple-600">
                        {competition.participant_count || '0'} 名
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500">ステータス:</span>
                      <span className={`ml-2 font-medium ${competition.is_active ? 'text-green-600' : 'text-gray-600'}`}>
                        {competition.is_active ? 'アクティブ' : '非アクティブ'}
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* 選択状況の表示 */}
        <div className="mt-6 p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center text-sm text-gray-600">
            <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
            <span>
              {selectedCompetitionId 
                ? `選択中: ${competitions.find(c => c.competition_id === selectedCompetitionId)?.name || '不明な大会'}`
                : showAllOption 
                  ? '選択中: 全大会のデータ（管理者権限）'
                  : '大会が選択されていません'
              }
            </span>
          </div>
        </div>
      </div>
    </Card>
  );

  const formatDate = (dateString: string | null) => {
    if (!dateString) return '日程未定';
    const date = new Date(dateString);
    return date.toLocaleDateString('ja-JP', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      weekday: 'short'
    });
  };
};

export default CompetitionSelector;  {competition.location && (
                      <div className="flex items-center">
                        <svg className="w-4 h-4 mr-1.5" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
                        </svg>
                        {competition.location}
                      </div>
                    )}
                  </div>