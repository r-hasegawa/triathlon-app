// triathlon-frontend/src/pages/SensorDataUpload/components/HeartRateUpload.tsx

import React, { useState, useRef } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { useFileUpload, UploadResult } from '../index';
import UploadResultCard from './UploadResultCard';
import { Input } from '@/components/ui/Input'; // <-- Inputコンポーネントをインポート

interface HeartRateUploadProps {
  competitionId: string;
  onUploadComplete: () => void;
}

const HeartRateUpload: React.FC<HeartRateUploadProps> = ({
  competitionId,
  onUploadComplete
}) => {
  const [files, setFiles] = useState<FileList | null>(null);
  const [results, setResults] = useState<UploadResult[]>([]);
  const [sensorId, setSensorId] = useState<string>(''); // <-- センサーID用のstateを追加
  const fileInputRef = useRef<HTMLInputElement>(null);
  // useFileUploadのupload関数を修正した前提で、第3引数でファイル名を指定
  const { upload, isLoading } = useFileUpload('/admin/upload/heart-rate');

  const handleUpload = async () => {
    // センサーIDが入力されていない場合は処理を中断
    if (!files || !sensorId) return;

    const additionalData = { sensor_id: sensorId };
    const { success, data } = await upload(files, competitionId, 'files', additionalData);

    if (success) {
      // 成功した場合、レスポンスの 'results' 配列を直接セット
      setResults(data.results || []);
    } else {
      // 失敗した場合、エラー情報を配列としてセット
      setResults([{
        file_name: files[0]?.name || 'ファイル',
        status: 'error',
        error: data.message || 'アップロードに失敗しました'
      }]);
    }

    resetFiles();
    onUploadComplete();
  };

  const resetFiles = () => {
    setFiles(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
    setSensorId('');
  };

  return (
    <Card className="p-6 border-l-4 border-l-red-500">
      <h2 className="text-xl font-semibold mb-4">3. 心拍データ（Garmin TCX）</h2>
      <div className="space-y-4">
        {/* センサーIDの入力欄 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            センサーID（手動入力）
          </label>
          <Input
            value={sensorId}
            onChange={(e) => setSensorId(e.target.value)}
            placeholder="例: GARMIN_001, HR_SENSOR_A など"
            className="w-full"
          />
          <p className="text-sm text-gray-500 mt-1">
            複数ファイルは同じセンサーIDに紐づけられます
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            TCXファイル（複数選択可能）
          </label>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".tcx,.xml"
            onChange={(e) => setFiles(e.target.files)}
            className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-red-500"
          />
          <p className="text-sm text-gray-500 mt-1">
            形式: TCX（XML）形式
          </p>
        </div>
        
        <Button 
          onClick={handleUpload}
          disabled={!files || !sensorId || isLoading} 
          className="w-full"
        >
          {isLoading ? '処理中...' : '心拍データをアップロード'}
        </Button>

        <UploadResultCard results={results} type="multiple" />
      </div>
    </Card>
  );
};

export default HeartRateUpload;