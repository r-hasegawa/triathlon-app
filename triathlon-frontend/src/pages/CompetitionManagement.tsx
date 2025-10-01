import React, { useState, useEffect } from 'react';
import { Layout } from '@/components/layout/Layout';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

interface Competition {
  competition_id: string;
  name: string;
  date: string;
  location: string;
  stats?: {
    participants: number;
    wbgt_records: number;
    mappings: number;
  };
}

interface DeleteConfirmation {
  competition_id: string;
  name: string;
}

export const CompetitionManagement: React.FC = () => {
  const [competitions, setCompetitions] = useState<Competition[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [newCompetition, setNewCompetition] = useState({
    name: '',
    date: '',
    location: ''
  });
  const [deleteConfirm, setDeleteConfirm] = useState<DeleteConfirmation | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    loadCompetitions();
  }, []);

  const loadCompetitions = async () => {
    setIsLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:8000/admin/competitions?include_stats=true', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      if (!response.ok) {
        console.error('Failed to load competitions:', response.status, response.statusText);
        return;
      }
      
      const data = await response.json();
      console.log('Loaded competitions data:', data);
      
      const competitionsArray = Array.isArray(data) ? data : (data.competitions || []);
      
      setCompetitions(competitionsArray);
    } catch (error) {
      console.error('Failed to load competitions:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const createCompetition = async () => {
    if (!newCompetition.name || !newCompetition.date) return;

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:8000/admin/competitions', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newCompetition),
      });

      if (response.ok) {
        setNewCompetition({ name: '', date: '', location: '' });
        loadCompetitions();
      } else {
        const error = await response.json();
        alert(`大会作成エラー: ${error.detail || '不明なエラー'}`);
      }
    } catch (error) {
      console.error('Failed to create competition:', error);
      alert('大会作成に失敗しました');
    }
  };

  const handleDeleteClick = (competition: Competition) => {
    setDeleteConfirm({
      competition_id: competition.competition_id,
      name: competition.name
    });
  };

  const confirmDelete = async () => {
    if (!deleteConfirm) return;

    setIsDeleting(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(
        `http://localhost:8000/admin/competitions/${deleteConfirm.competition_id}`,
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        const result = await response.json();
        console.log('Deletion result:', result);
        
        // 削除されたデータの詳細を表示
        const deletedData = result.deleted_data || {};
        const message = [
          `大会「${deleteConfirm.name}」を削除しました`,
          '',
          '削除されたデータ:',
          `・大会記録: ${deletedData.race_records || 0}件`,
          `・WBGT: ${deletedData.wbgt_records || 0}件`,
          `・マッピング: ${deletedData.mappings || 0}件`,
          `・体表温データ: ${deletedData.skin_temperature || 0}件`,
          `・カプセル体温データ: ${deletedData.core_temperature || 0}件`,
          `・心拍データ: ${deletedData.heart_rate || 0}件`,
          `・アップロードバッチ: ${deletedData.upload_batches || 0}件`
        ].join('\n');
        
        alert(message);
        
        loadCompetitions();
      } else {
        const error = await response.json();
        alert(`削除エラー: ${error.detail || '不明なエラー'}`);
      }
    } catch (error) {
      console.error('Failed to delete competition:', error);
      alert('大会削除に失敗しました');
    } finally {
      setIsDeleting(false);
      setDeleteConfirm(null);
    }
  };

  const cancelDelete = () => {
    setDeleteConfirm(null);
  };

  return (
    <Layout>
      <div className="space-y-6">
        <h1 className="text-2xl font-bold">大会管理</h1>
        
        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4">新規大会作成</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Input
              placeholder="大会名"
              value={newCompetition.name}
              onChange={(e) => setNewCompetition({...newCompetition, name: e.target.value})}
            />
            <Input
              type="date"
              value={newCompetition.date}
              onChange={(e) => setNewCompetition({...newCompetition, date: e.target.value})}
            />
            <Input
              placeholder="開催地"
              value={newCompetition.location}
              onChange={(e) => setNewCompetition({...newCompetition, location: e.target.value})}
            />
          </div>
          <Button
            onClick={createCompetition}
            className="mt-4"
            disabled={!newCompetition.name || !newCompetition.date}
          >
            作成
          </Button>
        </Card>

        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4">大会一覧</h2>
          {isLoading ? (
            <LoadingSpinner />
          ) : competitions.length === 0 ? (
            <p className="text-gray-500 text-center py-8">大会がありません</p>
          ) : (
            <div className="space-y-3">
              {competitions.map((comp) => (
                <div 
                  key={comp.competition_id} 
                  className="p-4 border rounded-lg hover:shadow-md transition-shadow bg-white"
                >
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <h3 className="font-semibold text-lg">{comp.name}</h3>
                      <p className="text-sm text-gray-600 mt-1">
                        📅 {comp.date} {comp.location && `| 📍 ${comp.location}`}
                      </p>
                      
                      {comp.stats && (
                        <div className="flex gap-4 mt-2 text-xs text-gray-500">
                          <span>👤 参加者: {comp.stats.participants}名</span>
                          <span>🌡️ WBGT: {comp.stats.wbgt_records}件</span>
                          <span>🔗 マッピング: {comp.stats.mappings}件</span>
                        </div>
                      )}
                    </div>
                    
                    <button
                      onClick={() => handleDeleteClick(comp)}
                      className="px-3 py-1 text-sm text-red-600 hover:text-red-700 hover:bg-red-50 rounded transition-colors"
                    >
                      削除
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        {deleteConfirm && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0 }}>
            <div className="bg-white rounded-lg shadow-xl p-6 max-w-md w-full mx-4">
              <div className="flex items-start gap-4">
                <div className="text-2xl">⚠️</div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold mb-2">大会の削除</h3>
                  <p className="text-gray-700 mb-4">
                    大会「<strong>{deleteConfirm.name}</strong>」を削除しますか?
                  </p>
                  <div className="bg-yellow-50 border border-yellow-200 rounded p-3 mb-4">
                    <p className="text-sm text-yellow-800">
                      ⚠️ この操作は取り消せません。<br />
                      大会に関連する以下のデータも削除されます:
                    </p>
                    <div className="text-sm text-yellow-800 mt-2 ml-2">
                      <div>• 大会記録（ゼッケン番号、タイム等）</div>
                      <div>• WBGTデータ</div>
                      <div>• センサーマッピング</div>
                      <div>• 体表温データ</div>
                      <div>• カプセル体温データ</div>
                      <div>• 心拍データ</div>
                      <div>• アップロードバッチ情報</div>
                    </div>
                  </div>
                  
                  <div className="flex gap-3">
                    <Button
                      onClick={confirmDelete}
                      disabled={isDeleting}
                      className="flex-1 bg-red-600 hover:bg-red-700 text-white"
                    >
                      {isDeleting ? '削除中...' : '削除する'}
                    </Button>
                    <Button
                      onClick={cancelDelete}
                      disabled={isDeleting}
                      variant="outline"
                      className="flex-1"
                    >
                      キャンセル
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};