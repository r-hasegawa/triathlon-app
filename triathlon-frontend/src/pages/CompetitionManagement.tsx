/**
 * 管理者用大会管理画面 - adminService使用版
 */

import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { adminService } from '@/services/adminService';

// 型定義
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

interface NewCompetition {
  name: string;
  date: string;
  location: string;
  description: string;
}

export const CompetitionManagement: React.FC = () => {
  const [competitions, setCompetitions] = useState<Competition[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [createLoading, setCreateLoading] = useState(false);
  const [newCompetition, setNewCompetition] = useState<NewCompetition>({
    name: '',
    date: '',
    location: '',
    description: ''
  });

  useEffect(() => {
    fetchCompetitions();
  }, []);

  const fetchCompetitions = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // ✅ adminService を使用して大会一覧を取得
      const data = await adminService.getCompetitions(true); // include_inactive=true
      setCompetitions(data);
      
    } catch (err) {
      console.error('Error fetching competitions:', err);
      setError('大会データの取得に失敗しました');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateCompetition = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!newCompetition.name.trim()) {
      alert('大会名は必須です');
      return;
    }

    try {
      setCreateLoading(true);
      
      // ✅ adminService を使用して大会を作成
      await adminService.createCompetition({
        name: newCompetition.name,
        date: newCompetition.date || null,
        location: newCompetition.location || null,
        description: newCompetition.description || null
      });

      // 成功時の処理
      setNewCompetition({ name: '', date: '', location: '', description: '' });
      setShowCreateForm(false);
      await fetchCompetitions(); // 一覧を再取得
      
      alert('大会が正常に作成されました');
      
    } catch (err: any) {
      console.error('Error creating competition:', err);
      alert(`大会作成に失敗しました: ${err.response?.data?.detail || err.message || '不明なエラー'}`);
    } finally {
      setCreateLoading(false);
    }
  };

  const handleDeleteCompetition = async (competitionId: string, competitionName: string) => {
    const confirmed = window.confirm(
      `大会「${competitionName}」を削除しますか？\n\n⚠️ この操作により、関連するすべてのデータ（センサデータ、大会記録など）が完全に削除されます。\n\nこの操作は取り消せません。`
    );

    if (!confirmed) return;

    try {
      // ✅ adminService を使用して大会を削除
      await adminService.deleteCompetition(competitionId);
      
      alert('大会が正常に削除されました');
      await fetchCompetitions(); // 一覧を再取得
      
    } catch (err: any) {
      console.error('Error deleting competition:', err);
      alert(`大会削除に失敗しました: ${err.response?.data?.detail || err.message || '不明なエラー'}`);
    }
  };

  const toggleCompetitionStatus = async (competitionId: string, currentStatus: boolean) => {
    try {
      // ✅ adminService を使用して大会ステータスを更新
      await adminService.updateCompetition(competitionId, {
        is_active: !currentStatus
      });

      await fetchCompetitions(); // 一覧を再取得
      
    } catch (err: any) {
      console.error('Error updating competition status:', err);
      alert(`大会ステータスの更新に失敗しました: ${err.response?.data?.detail || err.message || '不明なエラー'}`);
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
      <div className="flex items-center justify-center py-12">
        <LoadingSpinner size="lg" />
        <span className="ml-3 text-gray-600">大会データを読み込み中...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* ヘッダー */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">大会管理</h1>
          <p className="text-gray-600 mt-1">トライアスロン大会の作成・管理を行います</p>
        </div>
        <Button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="flex items-center"
        >
          <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clipRule="evenodd" />
          </svg>
          新規大会作成
        </Button>
      </div>

      {/* エラー表示 */}
      {error && (
        <Card className="p-4 border-red-200 bg-red-50">
          <div className="text-red-700">
            <p className="font-medium">エラーが発生しました</p>
            <p className="text-sm mt-1">{error}</p>
            <Button 
              onClick={fetchCompetitions}
              className="mt-2 text-sm"
              variant="outline"
            >
              再試行
            </Button>
          </div>
        </Card>
      )}

      {/* 大会作成フォーム */}
      {showCreateForm && (
        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4">新規大会作成</h2>
          <form onSubmit={handleCreateCompetition} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                label="大会名 *"
                value={newCompetition.name}
                onChange={(e) => setNewCompetition(prev => ({ ...prev, name: e.target.value }))}
                required
                placeholder="例: 第1回東京湾トライアスロン2025"
              />
              <Input
                label="開催日"
                type="date"
                value={newCompetition.date}
                onChange={(e) => setNewCompetition(prev => ({ ...prev, date: e.target.value }))}
              />
            </div>
            <Input
              label="開催地"
              value={newCompetition.location}
              onChange={(e) => setNewCompetition(prev => ({ ...prev, location: e.target.value }))}
              placeholder="例: 東京都江東区お台場海浜公園"
            />
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                大会説明
              </label>
              <textarea
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                rows={3}
                value={newCompetition.description}
                onChange={(e) => setNewCompetition(prev => ({ ...prev, description: e.target.value }))}
                placeholder="大会の概要や特記事項を入力してください"
              />
            </div>
            
            <div className="flex gap-3 pt-4">
              <Button
                type="submit"
                disabled={createLoading}
                className="flex items-center"
              >
                {createLoading && <LoadingSpinner size="sm" className="mr-2" />}
                作成
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowCreateForm(false)}
                disabled={createLoading}
              >
                キャンセル
              </Button>
            </div>
          </form>
        </Card>
      )}

      {/* 大会一覧 */}
      <div className="space-y-4">
        {competitions.length === 0 ? (
          <Card className="p-8 text-center">
            <div className="text-gray-500">
              <svg className="w-12 h-12 mx-auto mb-4 text-gray-300" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M4 4a2 2 0 012-2h8a2 2 0 012 2v12a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm3 1h6v4H7V5zm8 8v2h1v-2h-1zm-2-2H7v4h6v-4z" clipRule="evenodd" />
              </svg>
              <p className="text-lg font-medium">大会がありません</p>
              <p className="text-sm mt-1">「新規大会作成」ボタンから最初の大会を作成してください</p>
            </div>
          </Card>
        ) : (
          competitions.map((competition) => (
            <Card key={competition.id} className="p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-semibold text-gray-900">
                      {competition.name}
                    </h3>
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
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-600 mb-4">
                    <div className="flex items-center">
                      <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd" />
                      </svg>
                      {formatDate(competition.date)}
                    </div>
                    {competition.location && (
                      <div className="flex items-center">
                        <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
                        </svg>
                        {competition.location}
                      </div>
                    )}
                    <div className="flex items-center">
                      <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      ID: {competition.competition_id}
                    </div>
                  </div>

                  {competition.description && (
                    <p className="text-sm text-gray-600 mb-4">
                      {competition.description}
                    </p>
                  )}

                  {/* 統計情報 */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 bg-gray-50 rounded-lg">
                    <div className="text-center">
                      <div className="text-xl font-bold text-blue-600">
                        {competition.participant_count || 0}
                      </div>
                      <div className="text-xs text-gray-500">参加者</div>
                    </div>
                    <div className="text-center">
                      <div className="text-xl font-bold text-green-600">
                        {competition.sensor_data_count?.toLocaleString() || 0}
                      </div>
                      <div className="text-xs text-gray-500">センサデータ</div>
                    </div>
                    <div className="text-center">
                      <div className="text-xl font-bold text-purple-600">
                        {new Date(competition.created_at).toLocaleDateString()}
                      </div>
                      <div className="text-xs text-gray-500">作成日</div>
                    </div>
                    <div className="text-center">
                      <div className="text-xl font-bold text-orange-600">
                        {competition.updated_at ? new Date(competition.updated_at).toLocaleDateString() : '-'}
                      </div>
                      <div className="text-xs text-gray-500">更新日</div>
                    </div>
                  </div>
                </div>

                {/* 操作ボタン */}
                <div className="ml-6 flex flex-col gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => toggleCompetitionStatus(competition.competition_id, competition.is_active)}
                  >
                    {competition.is_active ? '無効化' : '有効化'}
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="text-red-600 border-red-300 hover:bg-red-50"
                    onClick={() => handleDeleteCompetition(competition.competition_id, competition.name)}
                  >
                    削除
                  </Button>
                </div>
              </div>
            </Card>
          ))
        )}
      </div>
    </div>
  );
};

export default CompetitionManagement;