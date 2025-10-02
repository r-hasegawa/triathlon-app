// triathlon-frontend/src/pages/SensorDataUpload/components/WbgtUpload.tsx

import React, { useState, useRef } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { useFileUpload, UploadResult } from '../index';
import UploadResultCard from './UploadResultCard';

interface WbgtUploadProps {
  competitionId: string;
  onUploadComplete: () => void;
}

const WbgtUpload: React.FC<WbgtUploadProps> = ({
  competitionId,
  onUploadComplete
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<UploadResult | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { upload, isLoading } = useFileUpload('/admin/upload/wbgt');

  const handleUpload = async () => {
    if (!file) return;

    const { success, data } = await upload(file, competitionId, 'wbgt_file');
    
    setResult({
      ...data,
      file: file.name,
      status: success ? 'success' : 'error'
    });

    resetFile();
    onUploadComplete();
  };

  const resetFile = () => {
    setFile(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <Card className="p-6 border-l-4 border-l-orange-500">
      <h2 className="text-xl font-semibold mb-4">4. WBGT環境データ</h2>
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            CSVファイル（1大会あたり1ファイル）
          </label>
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-orange-500"
          />
          <p className="text-sm text-gray-500 mt-1">
            形式: 日付, 時刻, WBGT値, 気温, 相対湿度, 黒球温度
          </p>
        </div>
        
        <Button 
          onClick={handleUpload}
          disabled={!file || isLoading}
          className="w-full"
        >
          {isLoading ? '処理中...' : 'WBGTデータをアップロード'}
        </Button>

        <UploadResultCard results={result} type="single" />
      </div>
    </Card>
  );
};

export default WbgtUpload;