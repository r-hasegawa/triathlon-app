// triathlon-frontend/src/pages/SensorDataUpload.tsx

import React, { useState, useEffect, useRef } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { Layout } from '@/components/layout/Layout';

interface Competition {
  competition_id: string;
  name: string;
  date: string;
  location: string;
}

interface UploadResult {
  file: string;
  batch_id?: string;
  success?: number;
  failed?: number;
  total?: number;
  status: string;
  error?: string;
  sensor_ids?: string[];
  trackpoints_total?: number;
  sensors_found?: number;
}

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

export const SensorDataUpload: React.FC = () => {
  const [competitions, setCompetitions] = useState<Competition[]>([]);
  const [selectedCompetition, setSelectedCompetition] = useState('');
  const [uploadBatches, setUploadBatches] = useState<UploadBatch[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // 体表温アップロード
  const [skinTempFiles, setSkinTempFiles] = useState<FileList | null>(null);
  const [skinTempResults, setSkinTempResults] = useState<UploadResult[]>([]);
  const skinTempInputRef = useRef<HTMLInputElement>(null);

  // カプセル温アップロード
  const [coreTempFiles, setCoreTempFiles] = useState<FileList | null>(null);
  const [coreTempResults, setCoreTempResults] = useState<UploadResult[]>([]);
  const coreTempInputRef = useRef<HTMLInputElement>(null);

  // 心拍アップロード
  const [heartRateFiles, setHeartRateFiles] = useState<FileList | null>(null);
  const [heartRateSensorId, setHeartRateSensorId] = useState('');
  const [heartRateResults, setHeartRateResults] = useState<UploadResult[]>([]);
  const heartRateInputRef = useRef<HTMLInputElement>(null);

  // 🆕 WBGT アップロード
  const [wbgtFile, setWbgtFile] = useState<File | null>(null);
  const [wbgtResult, setWbgtResult] = useState<UploadResult | null>(null);
  const wbgtInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadCompetitions();
    loadUploadBatches();
  }, []);

  const resetSkinTempFiles = () => {
    if (skinTempInputRef.current) {
      skinTempInputRef.current.value = '';
    }
    setSkinTempFiles(null);
  };

  const resetCoreTempFiles = () => {
    if (coreTempInputRef.current) {
      coreTempInputRef.current.value = '';
    }
    setCoreTempFiles(null);
  };

  const resetHeartRateFiles = () => {
    if (heartRateInputRef.current) {
      heartRateInputRef.current.value = '';
    }
    setHeartRateFiles(null);
  };

  const resetWbgtFile = () => {
    if (wbgtInputRef.current) {
      wbgtInputRef.current.value = '';
    }
    setWbgtFile(null);
  };

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

  const loadUploadBatches = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:8000/admin/upload/batches', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setUploadBatches(data.batches || []);
      }
    } catch (error) {
      console.error('Failed to load upload batches:', error);
    }
  };

  const uploadSkinTemperature = async () => {
    if (!selectedCompetition || !skinTempFiles) return;

    setIsLoading(true);
    try {
      const formData = new FormData();
      formData.append('competition_id', selectedCompetition);
      
      for (let i = 0; i < skinTempFiles.length; i++) {
        formData.append('files', skinTempFiles[i]);
      }

      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:8000/admin/upload/skin-temperature', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      const data = await response.json();
      setSkinTempResults(data.results || []);
      resetSkinTempFiles();
      loadUploadBatches();
    } catch (error) {
      console.error('Upload failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const uploadCoreTemperature = async () => {
    if (!selectedCompetition || !coreTempFiles) return;

    setIsLoading(true);
    try {
      const formData = new FormData();
      formData.append('competition_id', selectedCompetition);
      
      for (let i = 0; i < coreTempFiles.length; i++) {
        formData.append('files', coreTempFiles[i]);
      }

      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:8000/admin/upload/core-temperature', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      const data = await response.json();
      setCoreTempResults(data.results || []);
      resetCoreTempFiles();
      loadUploadBatches();
    } catch (error) {
      console.error('Upload failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const uploadHeartRate = async () => {
    if (!selectedCompetition || !heartRateFiles || !heartRateSensorId) return;

    setIsLoading(true);
    try {
      const formData = new FormData();
      formData.append('competition_id', selectedCompetition);
      formData.append('sensor_id', heartRateSensorId);
      
      for (let i = 0; i < heartRateFiles.length; i++) {
        formData.append('files', heartRateFiles[i]);
      }

      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:8000/admin/upload/heart-rate', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      const data = await response.json();
      setHeartRateResults(data.results || []);
      resetHeartRateFiles();
      loadUploadBatches();
    } catch (error) {
      console.error('Upload failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const uploadWbgt = async () => {
    if (!selectedCompetition || !wbgtFile) return;

    setIsLoading(true);
    try {
      const formData = new FormData();
      formData.append('competition_id', selectedCompetition);
      formData.append('wbgt_file', wbgtFile);
      formData.append('overwrite', 'true');

      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:8000/admin/upload/wbgt', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      const result = await response.json();

      if (response.ok) {
        setWbgtResult({
          status: 'success',
          file: wbgtFile.name,
          success: result.processed_records || result.success_records,
          failed: result.failed_records || 0,
          total: result.total_records,
          message: result.message
        });
        resetWbgtFile();
        loadUploadBatches();
      } else {
        setWbgtResult({
          status: 'error',
          file: wbgtFile.name,
          error: result.detail || 'アップロードに失敗しました'
        });
      }
    } catch (error) {
      console.error('WBGT upload failed:', error);
      setWbgtResult({
        status: 'error',
        file: wbgtFile.name,
        error: 'アップロードエラーが発生しました'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const deleteBatch = async (batchId: string) => {
    if (!confirm('このバッチとすべてのデータを削除しますか？')) return;

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`http://localhost:8000/admin/upload/batch/${batchId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        loadUploadBatches();
        alert('バッチが削除されました');
      }
    } catch (error) {
      console.error('Delete failed:', error);
      alert('削除に失敗しました');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success': return 'text-green-600';
      case 'partial': return 'text-yellow-600';
      case 'failed': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getSensorTypeLabel = (type: string) => {
    switch (type) {
      case 'skin_temperature': return '体表温';
      case 'core_temperature': return 'カプセル温';
      case 'heart_rate': return '心拍';
      case 'wbgt': return 'WBGT環境';  // 追加
      default: return type;
    }
  };

  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">🆕 実データ形式アップロード</h1>
            <p className="text-gray-600 mt-1">halshare・e-Celcius・TCX形式に対応</p>
          </div>
        </div>

        {/* 大会選択 */}
        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4">大会選択</h2>
          <select 
            value={selectedCompetition} 
            onChange={(e) => setSelectedCompetition(e.target.value)}
            className="w-full p-2 border border-gray-300 rounded-md"
          >
            <option value="">大会を選択してください</option>
            {competitions.map(comp => (
              <option key={comp.competition_id} value={comp.competition_id}>
                {comp.name} ({comp.date})
              </option>
            ))}
          </select>
        </Card>

        {selectedCompetition && (
          <>
            {/* 1. 体表温データアップロード */}
            <Card className="p-6 border-l-4 border-l-blue-500">
              <h2 className="text-lg font-semibold mb-4">1. 体表温データ（halshare）</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    CSVファイル（複数選択可能）
                  </label>
                  <input
                    ref={skinTempInputRef}
                    type="file"
                    multiple
                    accept=".csv"
                    onChange={(e) => setSkinTempFiles(e.target.files)}
                    className="w-full p-2 border border-gray-300 rounded-md"
                  />
                  <p className="text-sm text-gray-500 mt-1">
                    形式: halshareWearerName, halshareId, datetime, temperature
                  </p>
                </div>
                
                <Button 
                  onClick={uploadSkinTemperature}
                  disabled={!skinTempFiles || isLoading}
                  className="w-full"
                >
                  {isLoading ? '処理中...' : '体表温データをアップロード'}
                </Button>

                {skinTempResults.length > 0 && (
                  <div className="space-y-2">
                    <h3 className="font-medium">アップロード結果</h3>
                    {skinTempResults.map((result, idx) => (
                      <div key={idx} className={`p-3 rounded border ${result.status === 'success' ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
                        <div className="font-medium">{result.file}</div>
                        {result.error ? (
                          <div className="text-red-600 text-sm">{result.error}</div>
                        ) : (
                          <div className="text-sm">
                            成功: {result.success} / 失敗: {result.failed} / 合計: {result.total}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </Card>

            {/* 2. カプセル温データアップロード */}
            <Card className="p-6 border-l-4 border-l-green-500">
              <h2 className="text-lg font-semibold mb-4">2. カプセル体温データ（e-Celcius）</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    CSVファイル（複数選択可能）
                  </label>
                  <input
                    ref={coreTempInputRef}
                    type="file"
                    multiple
                    accept=".csv"
                    onChange={(e) => setCoreTempFiles(e.target.files)}
                    className="w-full p-2 border border-gray-300 rounded-md"
                  />
                  <p className="text-sm text-gray-500 mt-1">
                    形式: 1-3個のセンサーデータが5列ごとに並列配置
                  </p>
                </div>
                
                <Button 
                  onClick={uploadCoreTemperature}
                  disabled={!coreTempFiles || isLoading}
                  className="w-full"
                >
                  {isLoading ? '処理中...' : 'カプセル温データをアップロード'}
                </Button>

                {coreTempResults.length > 0 && (
                  <div className="space-y-2">
                    <h3 className="font-medium">アップロード結果</h3>
                    {coreTempResults.map((result, idx) => (
                      <div key={idx} className={`p-3 rounded border ${result.status === 'success' ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
                        <div className="font-medium">{result.file}</div>
                        {result.error ? (
                          <div className="text-red-600 text-sm">{result.error}</div>
                        ) : (
                          <div className="text-sm">
                            検出センサー: {result.sensor_ids?.join(', ')} | 
                            成功: {result.success} / 失敗: {result.failed}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </Card>

            {/* 3. 心拍データアップロード */}
            <Card className="p-6 border-l-4 border-l-purple-500">
              <h2 className="text-lg font-semibold mb-4">3. 心拍データ（Garmin TCX）</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    センサーID（手動入力）
                  </label>
                  <Input
                    value={heartRateSensorId}
                    onChange={(e) => setHeartRateSensorId(e.target.value)}
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
                    ref={heartRateInputRef}
                    type="file"
                    multiple
                    accept=".tcx"
                    onChange={(e) => setHeartRateFiles(e.target.files)}
                    className="w-full p-2 border border-gray-300 rounded-md"
                  />
                </div>
                
                <Button 
                  onClick={uploadHeartRate}
                  disabled={!heartRateFiles || !heartRateSensorId || isLoading}
                  className="w-full"
                >
                  {isLoading ? '処理中...' : '心拍データをアップロード'}
                </Button>

                {heartRateResults.length > 0 && (
                  <div className="space-y-2">
                    <h3 className="font-medium">アップロード結果</h3>
                    {heartRateResults.map((result, idx) => (
                      <div key={idx} className={`p-3 rounded border ${result.status === 'success' ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
                        <div className="font-medium">{result.file}</div>
                        {result.error ? (
                          <div className="text-red-600 text-sm">{result.error}</div>
                        ) : (
                          <div className="text-sm">
                            センサーID: {heartRateSensorId} | 
                            成功: {result.success} / 失敗: {result.failed}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </Card>

            {/* 4. WBGTデータアップロード */}
            <Card className="p-6 border-l-4 border-l-orange-500">
              <h2 className="text-lg font-semibold mb-4">4. WBGTデータ</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    CSVファイル（1つ）
                  </label>
                  <input
                    ref={wbgtInputRef}
                    type="file"
                    accept=".csv"
                    onChange={(e) => setWbgtFile(e.target.files ? e.target.files[0] : null)}
                    className="w-full p-2 border border-gray-300 rounded-md"
                  />
                  <p className="text-sm text-gray-500 mt-1">
                    WBGT計測器から出力されたCSVファイルをアップロードしてください
                  </p>
                </div>
                
                <Button 
                  onClick={uploadWbgt}
                  disabled={!wbgtFile || isLoading}
                  className="w-full"
                >
                  {isLoading ? '処理中...' : 'WBGTデータをアップロード'}
                </Button>

                {wbgtResult && (
                  <div className={`p-3 rounded border ${wbgtResult.status === 'success' ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
                    <div className="font-medium">{wbgtResult.file}</div>
                    {wbgtResult.error ? (
                      <div className="text-red-600 text-sm">{wbgtResult.error}</div>
                    ) : (
                      <div className="text-sm">
                        {wbgtResult.message || `成功: ${wbgtResult.success} / 失敗: ${wbgtResult.failed}`}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </Card>

          </>
        )}

        {/* アップロード履歴・バッチ管理 */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">アップロード履歴</h2>
            <Button onClick={loadUploadBatches} variant="outline" size="sm">
              更新
            </Button>
          </div>

          {uploadBatches.length === 0 ? (
            <p className="text-gray-500">アップロード履歴がありません</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full border-collapse border border-gray-300">
                <thead>
                  <tr className="bg-gray-50">
                    <th className="border border-gray-300 px-4 py-2 text-left">ファイル名</th>
                    <th className="border border-gray-300 px-4 py-2 text-left">種類</th>
                    <th className="border border-gray-300 px-4 py-2 text-left">レコード数</th>
                    <th className="border border-gray-300 px-4 py-2 text-left">ステータス</th>
                    <th className="border border-gray-300 px-4 py-2 text-left">アップロード日時</th>
                    <th className="border border-gray-300 px-4 py-2 text-left">操作</th>
                  </tr>
                </thead>
                <tbody>
                  {uploadBatches.map((batch) => (
                    <tr key={batch.batch_id}>
                      <td className="border border-gray-300 px-4 py-2">{batch.file_name}</td>
                      <td className="border border-gray-300 px-4 py-2">
                        {getSensorTypeLabel(batch.sensor_type)}
                      </td>
                      <td className="border border-gray-300 px-4 py-2">
                        成功:{batch.success_records} / 失敗:{batch.failed_records}
                      </td>
                      <td className={`border border-gray-300 px-4 py-2 ${getStatusColor(batch.status)}`}>
                        {batch.status}
                      </td>
                      <td className="border border-gray-300 px-4 py-2">
                        {new Date(batch.uploaded_at).toLocaleString('ja-JP')}
                      </td>
                      <td className="border border-gray-300 px-4 py-2">
                        <Button
                          onClick={() => deleteBatch(batch.batch_id)}
                          variant="outline"
                          size="sm"
                          className="text-red-600 hover:bg-red-50"
                        >
                          削除
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      </div>
    </Layout>
  );
};