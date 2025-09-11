import React, { useState, useEffect } from 'react';
import { Layout } from '@/components/layout/Layout';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

interface UploadBatch {
  batch_id: string;
  sensor_type: string;
  file_name: string;
  total_records: number;
  success_records: number;
  failed_records: number;
  status: string;
  uploaded_at: string;
  uploaded_by: string;
}

export const UploadHistory: React.FC = () => {
  const [batches, setBatches] = useState<UploadBatch[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    loadBatches();
  }, []);

  const loadBatches = async () => {
    setIsLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:8000/admin/upload/batches', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      const data = await response.json();
      setBatches(data.batches || []);
    } catch (error) {
      console.error('Failed to load upload batches:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const deleteBatch = async (batchId: string) => {
    if (!confirm('このバッチを削除しますか？')) return;

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`http://localhost:8000/admin/upload/batches/${batchId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        loadBatches();
      }
    } catch (error) {
      console.error('Failed to delete batch:', error);
    }
  };

  return (
    <Layout>
      <div className="space-y-6">
        <h1 className="text-2xl font-bold">アップロード履歴</h1>
        
        <Card className="p-6">
          {isLoading ? (
            <LoadingSpinner />
          ) : (
            <div className="space-y-4">
              {batches.map((batch) => (
                <div key={batch.batch_id} className="p-4 border rounded">
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="font-semibold">{batch.file_name}</h3>
                      <p className="text-sm text-gray-600">
                        {batch.sensor_type} - {batch.uploaded_at}
                      </p>
                      <p className="text-sm">
                        成功: {batch.success_records} / 失敗: {batch.failed_records} / 
                        総数: {batch.total_records}
                      </p>
                    </div>
                    <Button
                      variant="outline"
                      onClick={() => deleteBatch(batch.batch_id)}
                    >
                      削除
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </Layout>
  );
};