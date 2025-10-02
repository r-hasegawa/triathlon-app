// triathlon-frontend/src/pages/SensorDataUpload/components/RaceRecordUpload.tsx

import React, { useState, useRef } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { RaceRecordsUploadResult } from '../index';
import UploadResultCard from './UploadResultCard';

interface RaceRecordUploadProps {
  competitionId: string;
  onUploadComplete: () => void;
}

const RaceRecordUpload: React.FC<RaceRecordUploadProps> = ({
  competitionId,
  onUploadComplete
}) => {
  const [files, setFiles] = useState<FileList | null>(null);
  const [result, setResult] = useState<RaceRecordsUploadResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleUpload = async () => {
    if (!files) return;

    setIsLoading(true);
    try {
      const formData = new FormData();
      formData.append('competition_id', competitionId);
      
      for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
      }

      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:8000/admin/upload/race-records', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });

      const data = await response.json();

      if (response.ok) {
        setResult(data);
        resetFiles();
        onUploadComplete();
      } else {
        alert(data.detail || 'アップロードに失敗しました');
      }
    } catch (error) {
      console.error('大会記録アップロードエラー:', error);
      alert('アップロードエラーが発生しました');
    } finally {
      setIsLoading(false);
    }
  };

  const resetFiles = () => {
    setFiles(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <Card className="p-6 border-l-4 border-l-green-500">
      <h2 className="text-xl font-semibold mb-4">6. 大会記録データ</h2>
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            CSVファイル（複数選択可能）
          </label>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".csv"
            onChange={(e) => setFiles(e.target.files)}
            className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500"
          />
          <p className="text-sm text-gray-500 mt-1">
            複数のCSVファイルをゼッケン番号で統合します
          </p>
        </div>

        <Button 
          onClick={handleUpload}
          disabled={!files || isLoading}
          className="w-full"
        >
          {isLoading ? '処理中...' : '大会記録アップロード'}
        </Button>

        <UploadResultCard results={result} type="race-records" />
      </div>
    </Card>
  );
};

export default RaceRecordUpload;