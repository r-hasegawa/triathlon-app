// triathlon-frontend/src/pages/SensorDataUpload/components/CoreTemperatureUpload.tsx

import React, { useState, useRef } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { useFileUpload, UploadResult } from '../index';
import UploadResultCard from './UploadResultCard';

interface CoreTemperatureUploadProps {
  competitionId: string;
  onUploadComplete: () => void;
}

const CoreTemperatureUpload: React.FC<CoreTemperatureUploadProps> = ({
  competitionId,
  onUploadComplete
}) => {
  const [files, setFiles] = useState<FileList | null>(null);
  const [results, setResults] = useState<UploadResult[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { upload, isLoading } = useFileUpload('/admin/upload/core-temperature');

  const handleUpload = async () => {
    if (!files) return;

    // まとめてアップロード（旧コードと同じ挙動）
    const { success, data } = await upload(files, competitionId, 'files');

    // バックエンドは data.results で返す想定なのでそこを使う
    setResults(data.results || [
      {
        ...data,
        status: success ? 'success' : 'error'
      }
    ]);

    resetFiles();
    onUploadComplete();
  };

  const resetFiles = () => {
    setFiles(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <Card className="p-6 border-l-4 border-l-purple-500">
      <h2 className="text-xl font-semibold mb-4">2. カプセル温データ（e-Celcius）</h2>
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
            className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500"
          />
          <p className="text-sm text-gray-500 mt-1">
            形式: capsule_id, monitor_id, datetime, temperature, status
          </p>
        </div>
        
        <Button 
          onClick={handleUpload}
          disabled={!files || isLoading}
          className="w-full"
        >
          {isLoading ? '処理中...' : 'カプセル温データをアップロード'}
        </Button>

        <UploadResultCard results={results} type="multiple" />
      </div>
    </Card>
  );
};

export default CoreTemperatureUpload;