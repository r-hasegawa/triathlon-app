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
}

export const CompetitionManagement: React.FC = () => {
  const [competitions, setCompetitions] = useState<Competition[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [newCompetition, setNewCompetition] = useState({
    name: '',
    date: '',
    location: ''
  });

  useEffect(() => {
    loadCompetitions();
  }, []);

  const loadCompetitions = async () => {
    setIsLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:8000/admin/competitions', {
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
      
      // バックエンドのレスポンス形式に合わせて修正
      // data が配列の場合はそのまま、オブジェクトの場合は competitions プロパティから取得
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
      }
    } catch (error) {
      console.error('Failed to create competition:', error);
    }
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
          ) : (
            <div className="space-y-2">
              {competitions.map((comp) => (
                <div key={comp.competition_id} className="p-4 border rounded">
                  <h3 className="font-semibold">{comp.name}</h3>
                  <p className="text-sm text-gray-600">{comp.date} - {comp.location}</p>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </Layout>
  );
};