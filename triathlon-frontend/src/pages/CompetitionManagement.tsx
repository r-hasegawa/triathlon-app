/**
 * CompetitionManagement.tsx - エンドポイント規則対応版
 */

import React, { useState, useEffect } from 'react';
import { Layout } from '@/components/layout/Layout';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
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
      
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:8000/admin/competitions?include_inactive=true', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
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

  const handleCreateCompetition = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!newCompetition.name.trim()) {
      alert('大会名は必須です');
      return;
    }

    try {
      setCreateLoading(true);
      
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:8000/admin/competitions', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name: newCompetition.name,
          date: newCompetition.date || null,
          location: newCompetition.location || null,
          description: newCompetition.description || null
        })
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
      }

      setNewCompetition({ name: '', date: '', location: '', description: '' });
      setShowCreateForm(false);
      await fetchCompetitions();
      
      alert('大会が正常に作成されました');
      
    } catch (err) {
      console.error('Error creating competition:', err);
      alert('大会の作成に失敗しました');
    } finally {
      setCreateLoading(false);
    }
  };

  const handleDeleteCompetition = async (competitionId: string) => {
    if (!confirm('この大会を削除しますか？関連するすべてのデータも削除されます。')) {
      return;
    }

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`http://localhost:8000/admin/competitions/${competitionId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
      }

      await fetchCompetitions();
      alert('大会が削除されました');
      
    } catch (err) {
      console.error('Error deleting competition:', err);
      alert('大会の削除に失敗しました');
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex justify-center items-center py-12">
          <LoadingSpinner size="lg" />
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-8">
        <div className="bg-gradient-to-r from-green-600 to-green-700 rounded-lg p-8">
          <h1 className="text-3xl font-bold text-white mb-2">大会管理</h1>
          <p className="text-green-100">大会の作成・編集・削除</p>
        </div>

        {error && (
          <Card className="p-6 border-red-200 bg-red-50">
            <div className="text-red-700 text-center">
              <p className="font-medium">エラーが発生しました</p>
              <p className="text-sm mt-1">{error}</p>
              <Button onClick={fetchCompetitions} className="mt-3">
                再読み込み
              </Button>
            </div>
          </Card>
        )}

        <div className="flex justify-between items-center">
          <h2 className="text-xl font-semibold text-gray-900">大会一覧</h2>
          <Button
            onClick={() => setShowCreateForm(!showCreateForm)}
            className="bg-green-600 hover:bg-green-700"
          >
            {showCreateForm ? 'キャンセル' : '新規大会作成'}
          </Button>
        </div>

        {showCreateForm && (
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">新規大会作成</h3>
            <form onSubmit={handleCreateCompetition} className="space-y-4">
              <Input
                label="大会名"
                value={newCompetition.name}
                onChange={(e) => setNewCompetition(prev => ({ ...prev, name: e.target.value }))}
                placeholder="例: 2025年トライアスロン大会"
                required
              />
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  label="開催日"
                  type="date"
                  value={newCompetition.date}
                  onChange={(e) => setNewCompetition(prev => ({ ...prev, date: e.target.value }))}
                />
                <Input
                  label="開催地"
                  value={newCompetition.location}
                  onChange={(e) => setNewCompetition(prev => ({ ...prev, location: e.target.value }))}
                  placeholder="例: 東京都江東区お台場海浜公園"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  大会説明
                </label>
                <textarea
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
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
                  className="flex items-center bg-green-600 hover:bg-green-700"
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
                    <div className="text-sm text-gray-600 space-y-1">
                      {competition.date && (
                        <p>📅 {new Date(competition.date).toLocaleDateString('ja-JP')}</p>
                      )}
                      {competition.location && (
                        <p>📍 {competition.location}</p>
                      )}
                      {competition.description && (
                        <p>📝 {competition.description}</p>
                      )}
                      <div className="flex gap-4 mt-2">
                        <span>👥 参加者: {competition.participant_count || 0}人</span>
                        <span>📊 センサーデータ: {competition.sensor_data_count || 0}件</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex flex-col gap-2 ml-4">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDeleteCompetition(competition.competition_id)}
                      className="text-red-600 border-red-300 hover:bg-red-50"
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
    </Layout>
  );
};