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

export const MultiSensorUpload: React.FC = () => {
  const [competitions, setCompetitions] = useState<Competition[]>([]);
  const [selectedCompetition, setSelectedCompetition] = useState('');
  const [files, setFiles] = useState<FileList | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<any[]>([]);

  useEffect(() => {
    loadCompetitions();
  }, []);

  const loadCompetitions = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:8000/admin/competitions', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      const data = await response.json();
      setCompetitions(data.competitions || []);
    } catch (error) {
      console.error('Failed to load competitions:', error);
    }
  };

  const handleUpload = async () => {
    if (!selectedCompetition || !files) return;

    setIsLoading(true);
    try {
      const formData = new FormData();
      formData.append('competition_id', selectedCompetition);
      
      for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
      }

      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:8000/admin/upload/multi-sensor', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      const data = await response.json();
      setResults(data.results || []);
    } catch (error) {
      console.error('Upload failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Layout>
      <div className="space-y-6">
        <h1 className="text-2xl font-bold">マルチセンサーアップロード</h1>
        
        <Card className="p-6">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">大会選択</label>
              <select
                value={selectedCompetition}
                onChange={(e) => setSelectedCompetition(e.target.value)}
                className="w-full p-2 border rounded"
              >
                <option value="">大会を選択してください</option>
                {competitions.map((comp) => (
                  <option key={comp.competition_id} value={comp.competition_id}>
                    {comp.name} ({comp.date})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">ファイル選択</label>
              <Input
                type="file"
                multiple
                accept=".csv,.tcx"
                onChange={(e) => setFiles(e.target.files)}
              />
            </div>

            <Button
              onClick={handleUpload}
              disabled={!selectedCompetition || !files || isLoading}
            >
              {isLoading ? <LoadingSpinner size="sm" /> : 'アップロード'}
            </Button>
          </div>
        </Card>

        {results.length > 0 && (
          <Card className="p-6">
            <h2 className="text-lg font-semibold mb-4">アップロード結果</h2>
            <div className="space-y-2">
              {results.map((result, index) => (
                <div key={index} className="p-4 border rounded">
                  <h3 className="font-semibold">{result.file}</h3>
                  <p className="text-sm">
                    ステータス: {result.status} | 
                    成功: {result.success || 0} | 
                    失敗: {result.failed || 0}
                  </p>
                  {result.error && (
                    <p className="text-red-600 text-sm">{result.error}</p>
                  )}
                </div>
              ))}
            </div>
          </Card>
        )}
      </div>
    </Layout>
  );
};