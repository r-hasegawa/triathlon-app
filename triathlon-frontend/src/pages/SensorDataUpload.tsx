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

interface SensorDetail {
  sensor_number: number;
  sensor_id: string;
  success_count: number;
  failed_count: number;
  total_count: number;
}

interface UploadResult {
  file?: string;
  file_name?: string;      // 🆕 追加
  batch_id?: string;
  success?: number;
  failed?: number;
  total?: number;
  total_success?: number;  // 🆕 追加
  total_failed?: number;   // 🆕 追加
  status: string;
  error?: string;
  sensor_ids?: string[];
  sensor_details?: SensorDetail[];  // 🆕 追加
  trackpoints_total?: number;
  sensors_found?: number;
  message?: string;
  processed?: number;
  skipped?: number;
  errors?: string[];
}

interface RaceRecordsUploadResult {
  success: boolean;
  message: string;
  batch_id: string;
  competition_id: string;
  competition_name: string;
  total_files: number;
  participants_count: number;
  total_records: number;
  deleted_old_records: number;
  errors?: string[];
  upload_time: string;
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

interface MappingStatus {
  total_mappings: number;
  active_mappings: number;
  total_users_with_mappings: number;
  fully_mapped_users: number;
  mappings_by_sensor_type: Record<string, number>;
  competition_id?: string;
}

interface RaceRecordStatus {
  total_records: number;
  mapped_records: number;
  unmapped_records: number;
  mapping_coverage: number;
  competitions?: Record<string, any>;
}

const CoreTemperatureUploadResults: React.FC<{ results: UploadResult[] }> = ({ results }) => {
  if (results.length === 0) return null;

  return (
    <div className="space-y-4 mt-4">
      <h3 className="font-semibold text-lg">アップロード結果</h3>
      
      {results.map((result, fileIdx) => {
        const fileName = result.file_name || result.file || `ファイル ${fileIdx + 1}`;
        const statusClass = 
          result.status === 'success' || result.status === 'SUCCESS'
            ? 'bg-green-50 border-green-300'
            : result.status === 'partial' || result.status === 'PARTIAL'
            ? 'bg-yellow-50 border-yellow-300'
            : 'bg-red-50 border-red-300';

        return (
          <div key={fileIdx} className={`rounded-lg border-2 p-4 ${statusClass}`}>
            {/* ファイル名とサマリー */}
            <div className="mb-3">
              <div className="font-bold text-lg mb-2">{fileName}</div>
              
              {result.error ? (
                <div className="text-red-700 font-medium">
                  ❌ エラー: {result.error}
                </div>
              ) : (
                <div className="flex gap-4 text-sm flex-wrap">
                  <span className="text-green-700 font-medium">
                    ✓ 成功: {result.total_success || result.success || 0}件
                  </span>
                  {(result.total_failed || result.failed) ? (
                    <span className="text-red-700 font-medium">
                      ✗ 失敗: {result.total_failed || result.failed}件
                    </span>
                  ) : null}
                  <span className="text-gray-600 text-xs">
                    Batch ID: {result.batch_id}
                  </span>
                </div>
              )}
            </div>

            {/* センサー詳細 */}
            {result.sensor_details && result.sensor_details.length > 0 && (
              <div className="space-y-2 mt-3 pt-3 border-t border-gray-300">
                {result.sensor_details.map((sensor) => (
                  <div
                    key={sensor.sensor_number}
                    className="bg-white rounded p-3 shadow-sm"
                  >
                    <div className="flex items-center justify-between flex-wrap gap-2">
                      <div className="flex-1 min-w-[200px]">
                        <div className="font-medium text-gray-900">
                          検出されたセンサー{sensor.sensor_number}
                        </div>
                        <div className="text-sm text-gray-600 font-mono mt-1">
                          {sensor.sensor_id}
                        </div>
                      </div>
                      
                      <div className="flex gap-4 text-sm">
                        <span className="text-green-600 font-medium">
                          成功: {sensor.success_count}
                        </span>
                        <span className="text-red-600 font-medium">
                          失敗: {sensor.failed_count}
                        </span>
                        <span className="text-gray-500">
                          合計: {sensor.total_count}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

const RaceRecordsUploadResults: React.FC<{ result: RaceRecordsUploadResult | null }> = ({ result }) => {
  if (!result) return null;

  const hasErrors = result.errors && result.errors.length > 0;

  return (
    <div className="mt-4">
      <div className={`rounded-lg border-2 p-4 ${
        result.success && !hasErrors
          ? 'bg-green-50 border-green-300'
          : hasErrors
          ? 'bg-yellow-50 border-yellow-300'
          : 'bg-red-50 border-red-300'
      }`}>
        {/* ヘッダー */}
        <div className="flex items-center justify-between mb-3">
          <h4 className="text-lg font-bold text-gray-900">
            {result.competition_name}
          </h4>
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${
            result.success ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
          }`}>
            {result.success ? '✓ 成功' : '✗ 失敗'}
          </span>
        </div>

        {/* メインメッセージ */}
        <div className="mb-3">
          <p className="text-xl font-bold text-gray-900">
            {result.participants_count}人分のデータ
          </p>
          <p className="text-sm text-gray-600">{result.message}</p>
        </div>

        {/* 詳細情報 */}
        <div className="flex flex-wrap gap-4 text-sm text-gray-600">
          <span>📁 ファイル数: {result.total_files}</span>
          <span>📝 総レコード数: {result.total_records}</span>
          {result.deleted_old_records > 0 && (
            <span className="text-orange-600">
              🗑️ 削除された旧データ: {result.deleted_old_records}件
            </span>
          )}
        </div>

        {/* バッチID */}
        <div className="mt-2 text-xs text-gray-500">
          Batch ID: {result.batch_id}
        </div>

        {/* エラー表示 */}
        {hasErrors && (
          <div className="mt-3 pt-3 border-t border-yellow-300">
            <h5 className="font-semibold text-sm text-yellow-800 mb-2">
              ⚠️ 警告 ({result.errors!.length}件)
            </h5>
            <ul className="space-y-1 text-sm text-yellow-700">
              {result.errors!.slice(0, 3).map((error, idx) => (
                <li key={idx}>• {error}</li>
              ))}
              {result.errors!.length > 3 && (
                <li className="text-gray-600">... 他 {result.errors!.length - 3}件</li>
              )}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};

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

  // WBGT アップロード
  const [wbgtFile, setWbgtFile] = useState<File | null>(null);
  const [wbgtResult, setWbgtResult] = useState<UploadResult | null>(null);
  const wbgtInputRef = useRef<HTMLInputElement>(null);

  // マッピング データ
  const [mappingFile, setMappingFile] = useState<File | null>(null);
  const [mappingResult, setMappingResult] = useState<UploadResult | null>(null);
  const [mappingStatus, setMappingStatus] = useState<MappingStatus | null>(null);
  const mappingInputRef = useRef<HTMLInputElement>(null);

  // 大会記録アップロード
  const [raceRecordFiles, setRaceRecordFiles] = useState<FileList | null>(null);
  const [raceRecordResults, setRaceRecordResults] = useState<UploadResult[]>([]);
  const [raceRecordStatus, setRaceRecordStatus] = useState<RaceRecordStatus | null>(null);
  const raceRecordInputRef = useRef<HTMLInputElement>(null);
  const [raceRecordResult, setRaceRecordResult] = useState<RaceRecordsUploadResult | null>(null);


  useEffect(() => {
    loadCompetitions();
    loadUploadBatches();
  }, []);

  // 大会選択時にマッピング状況を読み込み
  useEffect(() => {
    if (selectedCompetition) {
      loadMappingStatus();
    } else {
      setMappingStatus(null);
    }
  }, [selectedCompetition]);

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

  const resetMappingFile = () => {
    if (mappingInputRef.current) {
      mappingInputRef.current.value = '';
    }
    setMappingFile(null);
  };

  const loadCompetitions = async () => {
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
    }
  };


  const loadUploadBatches = async () => {
    try {
      const token = localStorage.getItem('access_token');
      // 修正: /admin/upload/batches → /admin/batches
      const response = await fetch('http://localhost:8000/admin/batches', {
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


  // マッピング状況読み込み
  const loadMappingStatus = async () => {
    if (!selectedCompetition) return;
    
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`http://localhost:8000/admin/mapping/status?competition_id=${selectedCompetition}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setMappingStatus(data);
      }
    } catch (error) {
      console.error('Failed to load mapping status:', error);
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

  const uploadWbgtData = async () => {
    if (!wbgtFile || !selectedCompetition) return;

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

  // マッピングデータアップロード
  const uploadMappingData = async () => {
    if (!mappingFile || !selectedCompetition) return;

    setIsLoading(true);
    try {
      const formData = new FormData();
      formData.append('mapping_file', mappingFile);
      formData.append('competition_id', selectedCompetition);
      formData.append('overwrite', 'true');

      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:8000/admin/upload/mapping', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      const result = await response.json();

      if (response.ok) {
        setMappingResult({
          status: 'success',
          file: mappingFile.name,
          processed: result.processed_records,
          skipped: result.skipped_records,
          total: result.total_records,
          message: result.message,
          errors: result.errors
        });
        
        resetMappingFile();
        loadUploadBatches();
        loadMappingStatus();
      } else {
        setMappingResult({
          status: 'error',
          file: mappingFile.name,
          error: result.detail || 'マッピングアップロードに失敗しました'
        });
      }
    } catch (error) {
      console.error('Mapping upload failed:', error);
      setMappingResult({
        status: 'error',
        file: mappingFile.name,
        error: 'アップロードエラーが発生しました'
      });
    } finally {
      setIsLoading(false);
    }
  };

  // マッピング適用
  const applyMapping = async () => {
    if (!selectedCompetition) return;
    
    if (!confirm('マッピングをセンサーデータに適用しますか？この操作は取り消せません。')) return;
    
    setIsLoading(true);
    try {
      const formData = new FormData();
      formData.append('competition_id', selectedCompetition);
      
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:8000/admin/mapping/apply', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      const result = await response.json();
      
      if (response.ok) {
        alert(`マッピング適用完了: ${result.applied_count}件のデータに適用されました`);
        loadMappingStatus();
      } else {
        alert(`エラー: ${result.detail}`);
      }
    } catch (error) {
      console.error('Mapping apply failed:', error);
      alert('マッピング適用中にエラーが発生しました');
    } finally {
      setIsLoading(false);
    }
  };

  const deleteBatch = async (batchId: string) => {
    if (!confirm('このバッチとすべてのデータを削除しますか？')) return;

    try {
      const token = localStorage.getItem('access_token');
      // 修正: /admin/upload/batch/{batchId} → /admin/batches/{batchId}
      const response = await fetch(`http://localhost:8000/admin/batches/${batchId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        loadUploadBatches();
        if (selectedCompetition) {
          loadMappingStatus();
        }
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
      case 'wbgt': return 'WBGT環境';
      case 'other': return 'マッピング';
      default: return type;
    }
  };


  const resetRaceRecordFiles = () => {
    if (raceRecordInputRef.current) {
      raceRecordInputRef.current.value = '';
    }
    setRaceRecordFiles(null);
    setRaceRecordResults([]);
  };

  const handleRaceRecordUpload = async () => {
    if (!raceRecordFiles || raceRecordFiles.length === 0) {
      alert('CSVファイルを選択してください');
      return;
    }

    if (!selectedCompetition) {
      alert('大会を選択してください');
      return;
    }

    setIsLoading(true);
    
    try {
      const formData = new FormData();
      formData.append('competition_id', selectedCompetition);
      formData.append('overwrite', 'true');
      
      Array.from(raceRecordFiles).forEach((file) => {
        formData.append('files', file);
      });

      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:8000/admin/upload/race-records', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData
      });

      const result = await response.json();

      if (response.ok) {
        setRaceRecordResult(result);
        resetRaceRecordFiles();
        loadUploadBatches();
      } else {
        alert(result.detail || 'アップロードに失敗しました');
      }
    } catch (error) {
      console.error('Race record upload failed:', error);
      alert('アップロードエラーが発生しました');
    } finally {
      setIsLoading(false);
    }
  };

return (
    <Layout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">実データ形式アップロード</h1>
            <p className="text-gray-600 mt-1">halshare・e-Celcius・TCX・WBGT・マッピング形式に対応</p>
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

        {/* マッピング状況表示 */}
        {mappingStatus && selectedCompetition && (
          <Card className="p-6 bg-blue-50">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-blue-800">マッピング状況</h2>
              <div className="flex gap-2">
                <Button onClick={loadMappingStatus} variant="outline" size="sm">
                  更新
                </Button>
                <Button 
                  onClick={applyMapping}
                  disabled={isLoading || mappingStatus.total_mappings === 0}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white"
                  size="sm"
                >
                  {isLoading ? '適用中...' : 'マッピング適用'}
                </Button>
              </div>
            </div>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">{mappingStatus.total_mappings}</div>
                <div className="text-sm text-gray-600">総マッピング数</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">{mappingStatus.active_mappings}</div>
                <div className="text-sm text-gray-600">アクティブ</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">{mappingStatus.total_users_with_mappings}</div>
                <div className="text-sm text-gray-600">マッピング済みユーザー</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-indigo-600">{mappingStatus.fully_mapped_users}</div>
                <div className="text-sm text-gray-600">完全マッピング</div>
              </div>
            </div>

            <div>
              <h3 className="font-medium mb-2">センサータイプ別マッピング数</h3>
              <div className="flex flex-wrap gap-2">
                {Object.entries(mappingStatus.mappings_by_sensor_type || {}).map(([type, count]) => (
                  <span key={type} className="px-3 py-1 bg-white rounded-full text-sm border">
                    {getSensorTypeLabel(type)}: {count as number}
                  </span>
                ))}
              </div>
            </div>
          </Card>
        )}

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

                <CoreTemperatureUploadResults results={coreTempResults} />

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
                            成功: {result.success} / 失敗: {result.failed} / 合計: {result.total}
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
              <h2 className="text-lg font-semibold mb-4">4. WBGT環境データ</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    CSVファイル
                  </label>
                  <input
                    ref={wbgtInputRef}
                    type="file"
                    accept=".csv"
                    onChange={(e) => setWbgtFile(e.target.files?.[0] || null)}
                    className="w-full p-2 border border-gray-300 rounded-md"
                  />
                  <p className="text-sm text-gray-500 mt-1">
                    形式: 日付, 時刻, WBGT値, 気温, 相対湿度, 黒球温度（6列）
                  </p>
                  <p className="text-sm text-blue-600 mt-1">
                    環境データは大会全体で共有されます
                  </p>
                </div>
                
                <Button 
                  onClick={uploadWbgtData}
                  disabled={!wbgtFile || isLoading}
                  className="w-full"
                >
                  {isLoading ? '処理中...' : 'WBGT環境データをアップロード'}
                </Button>

                {wbgtResult && (
                  <div className="space-y-2">
                    <h3 className="font-medium">アップロード結果</h3>
                    <div className={`p-3 rounded border ${wbgtResult.status === 'success' ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
                      <div className="font-medium">{wbgtResult.file}</div>
                      {wbgtResult.error ? (
                        <div className="text-red-600 text-sm">{wbgtResult.error}</div>
                      ) : (
                        <div className="space-y-1">
                          <div className="text-sm">
                            成功: {wbgtResult.success} / 失敗: {wbgtResult.failed} / 合計: {wbgtResult.total}
                          </div>
                          {wbgtResult.message && (
                            <div className="text-blue-600 text-sm">{wbgtResult.message}</div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </Card>

            {/* 5. マッピングデータアップロード */}
            <Card className="p-6 border-l-4 border-l-indigo-500">
              <h2 className="text-lg font-semibold mb-4">5. マッピングデータ</h2>
              <div className="space-y-4">
                
                {/* 🆕 拡張説明 */}
                <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4">
                  <h3 className="font-medium text-indigo-800 mb-2">📋 マッピングCSV構造（🆕 ゼッケン番号対応版）</h3>
                  <div className="text-sm text-indigo-700 space-y-2">
                    <div className="font-mono text-xs bg-white p-2 rounded border overflow-x-auto">
                      user_id,race_number,skin_temp_sensor_id,core_temp_sensor_id,heart_rate_sensor_id,subject_name
                    </div>
                    <ul className="space-y-1">
                      <li>• <strong>user_id</strong>: システム内のユーザーID（必須）</li>
                      <li>• <strong>race_number</strong>: 🆕 大会記録の"No."（ゼッケン番号）</li>
                      <li>• <strong>skin_temp_sensor_id</strong>: halshareセンサーID</li>
                      <li>• <strong>core_temp_sensor_id</strong>: e-CelciusセンサーID</li>
                      <li>• <strong>heart_rate_sensor_id</strong>: GarminセンサーID</li>
                      <li>• <strong>subject_name</strong>: 被験者名（任意）</li>
                    </ul>
                  </div>
                </div>

                {/* サンプル例 */}
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                  <h3 className="font-medium text-gray-800 mb-2">📝 サンプルデータ例</h3>
                  <div className="text-xs font-mono bg-white p-3 rounded border overflow-x-auto">
                    <div className="text-gray-600">user_id,race_number,skin_temp_sensor_id,core_temp_sensor_id,heart_rate_sensor_id,subject_name</div>
                    <div>user001,100,11000002010B17,23.10.8E.81,GARMIN_001,田中太郎</div>
                    <div>user002,101,11000002011B17,23.10.8E.82,GARMIN_002,佐藤花子</div>
                    <div>user003,102,11000002012B17,23.10.8E.83,GARMIN_003,山田次郎</div>
                  </div>
                </div>

                {/* 重要事項 */}
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <h3 className="font-medium text-yellow-800 mb-2">⚠️ 重要事項</h3>
                  <ul className="text-sm text-yellow-700 space-y-1">
                    <li>• <strong>race_number</strong>は大会記録CSVの"No."列と完全一致させる</li>
                    <li>• 全ての列が必須ではありません（空欄可）</li>
                    <li>• user_idは必須で、システムに登録済みのIDを使用</li>
                    <li>• マッピング適用により、ゼッケン番号↔ユーザーID の紐づけが実行される</li>
                  </ul>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    CSVファイル
                  </label>
                  <input
                    ref={mappingInputRef}
                    type="file"
                    accept=".csv"
                    onChange={(e) => setMappingFile(e.target.files?.[0] || null)}
                    className="w-full p-2 border border-gray-300 rounded-md"
                  />
                  <p className="text-sm text-indigo-600 mt-2">
                    🆕 ゼッケン番号対応: センサーIDとユーザーID、さらに大会記録の紐づけを行います
                  </p>
                </div>
                
                <Button 
                  onClick={uploadMappingData}
                  disabled={!mappingFile || isLoading}
                  className="w-full"
                >
                  {isLoading ? '処理中...' : 'マッピングデータをアップロード'}
                </Button>

                {mappingResult && (
                  <div className="space-y-2">
                    <h3 className="font-medium">アップロード結果</h3>
                    <div className={`p-3 rounded border ${mappingResult.status === 'success' ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
                      <div className="font-medium">{mappingResult.file}</div>
                      {mappingResult.error ? (
                        <div className="text-red-600 text-sm">{mappingResult.error}</div>
                      ) : (
                        <div className="space-y-1">
                          <div className="text-sm">
                            処理: {mappingResult.processed} / スキップ: {mappingResult.skipped} / 合計: {mappingResult.total}
                          </div>
                          {/* 🆕 ゼッケン番号マッピング結果表示 */}
                          {mappingResult.race_number_mappings > 0 && (
                            <div className="text-blue-600 text-sm">
                              🏃 ゼッケン番号マッピング: {mappingResult.race_number_mappings}件
                            </div>
                          )}
                          {mappingResult.message && (
                            <div className="text-blue-600 text-sm">{mappingResult.message}</div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* マッピング適用ボタン */}
                <div className="border-t pt-4">
                  <Button 
                    onClick={applyMapping}
                    disabled={isLoading || !mappingStatus || mappingStatus.total_mappings === 0}
                    className="w-full bg-green-600 hover:bg-green-700 text-white"
                    size="lg"
                  >
                    {isLoading ? '適用中...' : '🚀 マッピング適用（センサー + ゼッケン番号）'}
                  </Button>
                  <p className="text-xs text-gray-500 mt-1 text-center">
                    🆕 センサーデータと大会記録の両方にマッピングを適用します
                  </p>
                </div>
              </div>
            </Card>

            {/* 6. 大会記録アップロード */}
            <Card className="p-6 border-l-4 border-l-red-500 mb-6">
              <h2 className="text-lg font-semibold mb-4">6. 大会記録データ</h2>
              <div className="space-y-4">
                {/* ファイル選択 */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    CSVファイル（複数選択可能）
                  </label>
                  <input
                    ref={raceRecordInputRef}
                    type="file"
                    multiple
                    accept=".csv"
                    onChange={(e) => setRaceRecordFiles(e.target.files)}
                    className="w-full p-2 border border-gray-300 rounded-md"
                  />
                  <p className="text-sm text-gray-500 mt-1">
                    複数のCSVファイルをゼッケン番号で統合します
                  </p>
                </div>

                {/* アップロードボタン */}
                <Button 
                  onClick={handleRaceRecordUpload}
                  disabled={!raceRecordFiles || isLoading}
                  className="w-full"
                >
                  {isLoading ? '処理中...' : '大会記録アップロード'}
                </Button>

                {/* アップロード結果表示 */}
                <RaceRecordsUploadResults result={raceRecordResult} />

              </div>
            </Card>

          </>
        )}

        {/* アップロード履歴 */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">アップロード履歴</h2>
            <Button onClick={loadUploadBatches} variant="outline" size="sm">
              更新
            </Button>
          </div>
          
          {uploadBatches.length === 0 ? (
            <p className="text-gray-500 text-center py-8">アップロード履歴がありません</p>
          ) : (
            <div className="space-y-3">
              {uploadBatches.map((batch) => (
                <div key={batch.batch_id} className="p-4 border rounded-lg bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3">
                        <span className="font-medium">
                          {getSensorTypeLabel(batch.sensor_type)}
                        </span>
                        <span className={`font-semibold ${getStatusColor(batch.status)}`}>
                          {batch.status}
                        </span>
                      </div>
                      <div className="text-sm text-gray-600 mt-1">
                        {batch.file_name} - {new Date(batch.uploaded_at).toLocaleString('ja-JP')}
                      </div>
                      <div className="text-sm mt-1">
                        成功: {batch.success_records} / 
                        失敗: {batch.failed_records} / 
                        合計: {batch.total_records}
                      </div>
                    </div>
                    <Button
                      onClick={() => deleteBatch(batch.batch_id)}
                      variant="outline"
                      size="sm"
                      className="text-red-600 border-red-300 hover:bg-red-50"
                    >
                      削除
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        {isLoading && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white p-6 rounded-lg shadow-lg">
              <LoadingSpinner size="lg" text="データを処理中..." />
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};