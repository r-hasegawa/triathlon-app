/**
 * マルチセンサー対応アップロード画面
 * センサー種別ごとの入力ページ
 */

import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { adminService } from '@/services/adminService';

// センサータイプ定義
enum SensorType {
  SKIN_TEMPERATURE = 'skin_temperature',
  CORE_TEMPERATURE = 'core_temperature',
  HEART_RATE = 'heart_rate',
  WBGT = 'wbgt'
}

interface SensorConfig {
  type: SensorType;
  name: string;
  description: string;
  icon: string;
  csvFormat: string[];
  example: string;
  mappingExample: string;
}

interface UploadStatus {
  isUploading: boolean;
  isMapping: boolean;
  lastUpload?: any;
  lastMapping?: any;
  unmappedCount: number;
  error?: string;
}

interface UnmappedSummary {
  total_unmapped_records: number;
  by_sensor_type: Record<string, {
    total_records: number;
    unique_sensors: number;
    sensor_ids: string[];
  }>;
  competition_id?: string;
}

const SENSOR_CONFIGS: SensorConfig[] = [
  {
    type: SensorType.SKIN_TEMPERATURE,
    name: '体表温データ（halshare）',
    description: '皮膚表面から測定される温度データ',
    icon: '🌡️',
    csvFormat: ['sensor_id', 'timestamp', 'temperature', 'location (optional)', 'ambient_temp (optional)'],
    example: 'SENSOR_001,2025-01-01 09:00:00,36.5,forehead,25.0',
    mappingExample: 'SENSOR_001,user001,田中太郎'
  },
  {
    type: SensorType.CORE_TEMPERATURE,
    name: 'カプセル体温データ（e-Celcius）',
    description: '体内で測定される核心温度データ',
    icon: '💊',
    csvFormat: ['sensor_id', 'timestamp', 'temperature', 'monitor_id', 'capsule_id', 'battery (optional)', 'signal (optional)'],
    example: 'CAPSULE_001,2025-01-01 09:00:00,37.2,MON_001,CAP_001,95,85',
    mappingExample: 'CAPSULE_001,user001,田中太郎'
  },
  {
    type: SensorType.HEART_RATE,
    name: '心拍データ（Garmin）',
    description: 'ウェアラブルデバイスから取得される心拍数データ',
    icon: '❤️',
    csvFormat: ['sensor_id', 'timestamp', 'heart_rate', 'hr_zone (optional)', 'rr_interval (optional)', 'activity (optional)', 'calories (optional)'],
    example: 'GARMIN_001,2025-01-01 09:00:00,145,3,650,running,250',
    mappingExample: 'GARMIN_001,user001,田中太郎'
  },
  {
    type: SensorType.WBGT,
    name: 'WBGT環境データ',
    description: '湿球黒球温度による環境測定データ',
    icon: '🌤️',
    csvFormat: ['sensor_id', 'timestamp', 'wbgt', 'air_temp (optional)', 'humidity (optional)', 'wind_speed (optional)', 'solar (optional)', 'location (optional)'],
    example: 'WBGT_001,2025-01-01 09:00:00,28.5,32.0,75,2.5,800,start_line',
    mappingExample: 'WBGT_001,,（環境データのためマッピング不要）'
  }
];

export const MultiSensorUpload: React.FC = () => {
  const [selectedCompetition, setSelectedCompetition] = useState<string>('');
  const [competitions, setCompetitions] = useState<any[]>([]);
  const [uploadStatuses, setUploadStatuses] = useState<Record<string, UploadStatus>>({});
  const [unmappedSummary, setUnmappedSummary] = useState<UnmappedSummary | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchCompetitions();
    fetchUnmappedSummary();
  }, [selectedCompetition]);

  const fetchCompetitions = async () => {
    try {
      const data = await adminService.getCompetitions(true);
      setCompetitions(data);
    } catch (error) {
      console.error('Error fetching competitions:', error);
    }
  };

  const fetchUnmappedSummary = async () => {
    try {
      setLoading(true);
      const summary = await adminService.getUnmappedDataSummary(selectedCompetition || undefined);
      setUnmappedSummary(summary);
      
      // 各センサータイプの未マッピング数を更新
      const newStatuses = { ...uploadStatuses };
      SENSOR_CONFIGS.forEach(config => {
        if (!newStatuses[config.type]) {
          newStatuses[config.type] = {
            isUploading: false,
            isMapping: false,
            unmappedCount: 0
          };
        }
        const typeData = summary?.by_sensor_type?.[config.type];
        newStatuses[config.type].unmappedCount = typeData?.total_records || 0;
      });
      setUploadStatuses(newStatuses);
    } catch (error) {
      console.error('Error fetching unmapped summary:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDataUpload = async (sensorType: SensorType, file: File) => {
    if (!file) return;

    setUploadStatuses(prev => ({
      ...prev,
      [sensorType]: { ...prev[sensorType], isUploading: true, error: undefined }
    }));

    try {
      // センサータイプごとのアップロードエンドポイント
      const endpoint = getUploadEndpoint(sensorType);
      const formData = new FormData();
      formData.append('data_file', file);
      if (selectedCompetition) {
        formData.append('competition_id', selectedCompetition);
      }

      const response = await fetch(`/api/multi-sensor/${endpoint}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Upload failed');
      }

      const result = await response.json();
      
      setUploadStatuses(prev => ({
        ...prev,
        [sensorType]: {
          ...prev[sensorType],
          isUploading: false,
          lastUpload: result
        }
      }));

      alert(`${getSensorName(sensorType)}データのアップロードが完了しました。\n処理レコード数: ${result.processed_records}`);
      
      // サマリー再取得
      await fetchUnmappedSummary();

    } catch (error) {
      console.error('Upload error:', error);
      const errorMessage = error instanceof Error ? error.message : 'アップロードに失敗しました';
      
      setUploadStatuses(prev => ({
        ...prev,
        [sensorType]: { 
          ...prev[sensorType], 
          isUploading: false,
          error: errorMessage
        }
      }));
      
      alert(`アップロードに失敗しました: ${errorMessage}`);
    }
  };

  const handleMappingUpload = async (sensorType: SensorType, mappingFile: File) => {
    if (!mappingFile) return;

    setUploadStatuses(prev => ({
      ...prev,
      [sensorType]: { ...prev[sensorType], isMapping: true, error: undefined }
    }));

    try {
      const endpoint = getMappingEndpoint(sensorType);
      const formData = new FormData();
      formData.append('mapping_file', mappingFile);
      if (selectedCompetition) {
        formData.append('competition_id', selectedCompetition);
      }

      const response = await fetch(`/api/multi-sensor/${endpoint}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Mapping failed');
      }

      const result = await response.json();
      
      setUploadStatuses(prev => ({
        ...prev,
        [sensorType]: {
          ...prev[sensorType],
          isMapping: false,
          lastMapping: result
        }
      }));

      alert(`${getSensorName(sensorType)}のマッピングが完了しました。\nマッピング適用: ${result.mapped_records}件`);
      
      // サマリー再取得
      await fetchUnmappedSummary();

    } catch (error) {
      console.error('Mapping error:', error);
      const errorMessage = error instanceof Error ? error.message : 'マッピングに失敗しました';
      
      setUploadStatuses(prev => ({
        ...prev,
        [sensorType]: { 
          ...prev[sensorType], 
          isMapping: false,
          error: errorMessage
        }
      }));
      
      alert(`マッピングに失敗しました: ${errorMessage}`);
    }
  };

  const getUploadEndpoint = (sensorType: SensorType): string => {
    const endpoints = {
      [SensorType.SKIN_TEMPERATURE]: 'upload/skin-temperature',
      [SensorType.CORE_TEMPERATURE]: 'upload/core-temperature',
      [SensorType.HEART_RATE]: 'upload/heart-rate',
      [SensorType.WBGT]: 'upload/wbgt'
    };
    return endpoints[sensorType];
  };

  const getMappingEndpoint = (sensorType: SensorType): string => {
    const endpoints = {
      [SensorType.SKIN_TEMPERATURE]: 'mapping/skin-temperature',
      [SensorType.CORE_TEMPERATURE]: 'mapping/core-temperature',
      [SensorType.HEART_RATE]: 'mapping/heart-rate',
      [SensorType.WBGT]: 'mapping/wbgt'
    };
    return endpoints[sensorType];
  };

  const getSensorName = (sensorType: SensorType): string => {
    const config = SENSOR_CONFIGS.find(c => c.type === sensorType);
    return config?.name || sensorType;
  };

  return (
    <div className="space-y-6">
      {/* ヘッダー */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">マルチセンサーデータ管理</h1>
          <p className="text-gray-600 mt-1">センサー種別ごとにデータをアップロードし、後からマッピングできます</p>
        </div>
        
        {/* 大会選択 */}
        <div className="w-64">
          <select
            value={selectedCompetition}
            onChange={(e) => setSelectedCompetition(e.target.value)}
            className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">全大会</option>
            {competitions.map(comp => (
              <option key={comp.competition_id} value={comp.competition_id}>
                {comp.competition_name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* 未マッピングデータサマリー */}
      {unmappedSummary && unmappedSummary.total_unmapped_records > 0 && (
        <Card className="bg-yellow-50 border-yellow-200">
          <div className="p-4">
            <div className="flex items-center mb-3">
              <span className="text-xl mr-2">⚠️</span>
              <h3 className="text-lg font-semibold text-yellow-800">
                未マッピングデータ: {unmappedSummary.total_unmapped_records}件
              </h3>
            </div>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              {SENSOR_CONFIGS.map(config => {
                const typeData = unmappedSummary.by_sensor_type?.[config.type];
                return (
                  <div key={config.type} className="text-center p-3 bg-white rounded-lg border">
                    <div className="text-2xl mb-1">{config.icon}</div>
                    <div className="text-xl font-bold text-orange-600">
                      {typeData?.total_records || 0}
                    </div>
                    <div className="text-xs text-gray-600">未マッピング</div>
                    <div className="text-xs text-gray-500 mt-1">
                      {typeData?.unique_sensors || 0} センサー
                    </div>
                  </div>
                );
              })}
            </div>
            
            <div className="text-sm text-yellow-700">
              ⚠️ 未マッピングデータは被験者に表示されません。マッピングファイルをアップロードしてください。
            </div>
          </div>
        </Card>
      )}

      {/* センサー種別ごとのアップロードセクション */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {SENSOR_CONFIGS.map(config => (
          <SensorUploadCard
            key={config.type}
            config={config}
            status={uploadStatuses[config.type] || { isUploading: false, isMapping: false, unmappedCount: 0 }}
            onDataUpload={(file) => handleDataUpload(config.type, file)}
            onMappingUpload={(file) => handleMappingUpload(config.type, file)}
          />
        ))}
      </div>
    </div>
  );
};

// === センサーアップロードカードコンポーネント ===

interface SensorUploadCardProps {
  config: SensorConfig;
  status: UploadStatus;
  onDataUpload: (file: File) => void;
  onMappingUpload: (file: File) => void;
}

const SensorUploadCard: React.FC<SensorUploadCardProps> = ({
  config,
  status,
  onDataUpload,
  onMappingUpload
}) => {
  const [dataFile, setDataFile] = useState<File | null>(null);
  const [mappingFile, setMappingFile] = useState<File | null>(null);
  const [showDetails, setShowDetails] = useState(false);

  const handleDataFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) setDataFile(file);
  };

  const handleMappingFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) setMappingFile(file);
  };

  return (
    <Card className="overflow-hidden">
      {/* ヘッダー */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <span className="text-2xl mr-3">{config.icon}</span>
            <div>
              <h3 className="text-lg font-semibold text-white">{config.name}</h3>
              <p className="text-blue-100 text-sm">{config.description}</p>
            </div>
          </div>
          <div className="text-right">
            {status.unmappedCount > 0 && (
              <div className="bg-yellow-500 text-white px-2 py-1 rounded-full text-xs font-medium">
                {status.unmappedCount} 未マッピング
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="p-6 space-y-4">
        {/* エラー表示 */}
        {status.error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-3">
            <div className="text-red-700 text-sm">
              ❌ {status.error}
            </div>
          </div>
        )}

        {/* データファイルアップロード */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            📊 センサーデータファイル (CSV)
          </label>
          <div className="flex gap-2">
            <input
              type="file"
              accept=".csv"
              onChange={handleDataFileChange}
              className="flex-1 text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
            />
            <Button
              onClick={() => dataFile && onDataUpload(dataFile)}
              disabled={!dataFile || status.isUploading}
              size="sm"
            >
              {status.isUploading ? <LoadingSpinner size="sm" /> : 'アップロード'}
            </Button>
          </div>
          {status.lastUpload && (
            <div className="mt-2 text-sm text-green-600">
              ✅ 最終アップロード: {status.lastUpload.processed_records}件処理完了
            </div>
          )}
        </div>

        {/* マッピングファイルアップロード */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            🔗 マッピングファイル (CSV)
          </label>
          <div className="flex gap-2">
            <input
              type="file"
              accept=".csv"
              onChange={handleMappingFileChange}
              className="flex-1 text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-medium file:bg-green-50 file:text-green-700 hover:file:bg-green-100"
            />
            <Button
              onClick={() => mappingFile && onMappingUpload(mappingFile)}
              disabled={!mappingFile || status.isMapping || status.unmappedCount === 0}
              size="sm"
              variant="outline"
            >
              {status.isMapping ? <LoadingSpinner size="sm" /> : 'マッピング適用'}
            </Button>
          </div>
          {status.lastMapping && (
            <div className="mt-2 text-sm text-green-600">
              ✅ 最終マッピング: {status.lastMapping.mapped_records}件適用完了
            </div>
          )}
          {status.unmappedCount === 0 && (
            <div className="mt-2 text-sm text-gray-500">
              ℹ️ 未マッピングデータがありません
            </div>
          )}
        </div>

        {/* CSV形式詳細 */}
        <div>
          <Button
            onClick={() => setShowDetails(!showDetails)}
            variant="outline"
            size="sm"
            className="text-xs"
          >
            {showDetails ? '🔼 CSV形式を隠す' : '🔽 CSV形式を表示'}
          </Button>
          
          {showDetails && (
            <div className="mt-3 p-3 bg-gray-50 rounded-md text-sm">
              <div className="font-medium text-gray-700 mb-2">必須列:</div>
              <div className="font-mono text-xs bg-white p-2 rounded border">
                {config.csvFormat.join(', ')}
              </div>
              <div className="font-medium text-gray-700 mt-3 mb-2">データ例:</div>
              <div className="font-mono text-xs bg-white p-2 rounded border text-green-600">
                {config.example}
              </div>
              <div className="font-medium text-gray-700 mt-3 mb-2">マッピング例:</div>
              <div className="font-mono text-xs bg-white p-2 rounded border text-blue-600">
                {config.mappingExample}
              </div>
              <div className="mt-2 text-xs text-gray-600">
                • (optional) の列は省略可能です<br/>
                • timestamp形式: YYYY-MM-DD HH:MM:SS<br/>
                • マッピングファイル形式: sensor_id, user_id, subject_name (optional)
              </div>
            </div>
          )}
        </div>
      </div>
    </Card>
  );
};

export default MultiSensorUpload;