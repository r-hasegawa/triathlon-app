// triathlon-frontend/src/pages/SensorDataUpload/components/SkinTemperatureUpload.tsx

import React, { useState, useRef } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { useFileUpload, UploadResult } from '../index';
import UploadResultCard from './UploadResultCard';

interface SkinTemperatureUploadProps {
  competitionId: string;
  onUploadComplete: () => void;
}

const SkinTemperatureUpload: React.FC<SkinTemperatureUploadProps> = ({
  competitionId,
  onUploadComplete
}) => {
  const [files, setFiles] = useState<FileList | null>(null);
  const [results, setResults] = useState<UploadResult[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { upload, isLoading } = useFileUpload('/admin/upload/skin-temperature');

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
    <Card className="p-6 border-l-4 border-l-blue-500">
      <h2 className="text-xl font-semibold mb-4">1. 体表温データ（halshare）</h2>
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
            className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
          />
          <p className="text-sm text-gray-500 mt-1">
            形式: halshareWearerName, halshareId, datetime, temperature
          </p>
        </div>
        
        <Button 
          onClick={handleUpload}
          disabled={!files || isLoading}
          className="w-full"
        >
          {isLoading ? '処理中...' : '体表温データをアップロード'}
        </Button>

        <UploadResultCard results={results} type="multiple" />
      </div>
    </Card>
  );
};

export default SkinTemperatureUpload;
