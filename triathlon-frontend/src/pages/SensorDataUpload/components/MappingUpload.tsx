// triathlon-frontend/src/pages/SensorDataUpload/components/MappingUpload.tsx

import React, { useState, useRef } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { useFileUpload, UploadResult } from '../index';
import UploadResultCard from './UploadResultCard';

interface MappingUploadProps {
  competitionId: string;
  onUploadComplete: () => void;
}

const MappingUpload: React.FC<MappingUploadProps> = ({
  competitionId,
  onUploadComplete
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<UploadResult | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { upload, isLoading } = useFileUpload('/admin/upload/mapping');

  const handleUpload = async () => {
    if (!file) return;

    const { success, data } = await upload(file, competitionId, 'mapping_file');
    
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
    <Card className="p-6 border-l-4 border-l-indigo-500">
      <h2 className="text-xl font-semibold mb-4">5. マッピングデータ</h2>
      <div className="space-y-4">
        <div className="bg-blue-50 p-4 rounded-lg">
          <h3 className="font-medium mb-2">📋 CSV形式</h3>
          <ul className="text-sm space-y-1 text-gray-700">
            <li>• ヘッダー行: User ID, 体表温センサID, カプセル温センサID, 心拍ID, 大会記録ID（ゼッケン番号）</li>
            <li>• 列名は仕様書と完全一致させる</li>
            <li>• 全ての列が必須ではありません（空欄可）</li>
            <li>• user_idは必須で、システムに登録済みのIDを使用</li>
          </ul>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            CSVファイル
          </label>
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500"
          />
          <p className="text-sm text-indigo-600 mt-2">
            センサーIDとユーザーID、大会記録の紐づけを行います
          </p>
        </div>
        
        <Button 
          onClick={handleUpload}
          disabled={!file || isLoading}
          className="w-full"
        >
          {isLoading ? '処理中...' : 'マッピングデータをアップロード'}
        </Button>

        <UploadResultCard results={result} type="single" />
      </div>
    </Card>
  );
};

export default MappingUpload;