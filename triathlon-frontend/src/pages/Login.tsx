/**
 * 完全版マルチセンサーアップロード画面
 * センサー種別ごとの独立したアップロード機能
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
  const [loading, setLoading] = useState(true);

  // 初期化
  useEffect(() => {
    initializeData();
  }, []);

  // 大会変更時のデータ更新
  useEffect(() => {
    if (competitions.length > 0) {
      fetchUnmappedSummary();
    }
  }, [selectedCompetition, competitions]);

  const initializeData = async () => {
    try {
      setLoading(true);
      await fetchCompetitions();
      initializeUploadStatuses();
    } catch (error) {
      console.error('Error initializing data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchCompetitions = async () => {
    try {
      const data = await adminService.getCompetitions(true);
      setCompetitions(data);
      
      // デフォルトで最新の大会を選択
      if (data.length > 0 && !selectedCompetition) {
        setSelectedCompetition(data[0].competition_id);
      }
    } catch (error) {
      console.error('Error fetching competitions:', error);
    }
  };

  const initializeUploadStatuses = () => {
    const initialStatuses: Record<string, UploadStatus> = {};
    SENSOR_CONFIGS.forEach(config => {
      initialStatuses[config.type] = {
        isUploading: false,
        isMapping: false,
        unmappedCount: 0
      };
    });
    setUploadStatuses(initialStatuses);
  };

  const fetchUnmappedSummary = async () => {
    try {
      // 実際のAPIは実装時に作成する必要があります
      // 暫定的にダミーデータを使用
      const summary: UnmappedSummary = {
        total_unmapped_records: 0,
        by_sensor_type: {},
        competition_id: selectedCompetition
      };

      // 各センサータイプのダミーデータ
      SENSOR_CONFIGS.forEach(config => {
        summary.by_sensor_type[config.type] = {
          total_records: Math.floor(Math.random() * 100),
          unique_sensors: Math.floor(Math.random() * 10),
          sensor_ids: [`${config.type.toUpperCase()}_001`, `${config.type.toUpperCase()}_002`]
        };
        summary.total_unmapped_records += summary.by_sensor_type[config.type].total_records;
      });

      setUnmappedSummary(summary);
      
      // 未マッピング数を更新
      const newStatuses = { ...uploadStatuses };
      SENSOR_CONFIGS.forEach(config => {
        if (newStatuses[config.type]) {
          const typeData = summary.by_sensor_type[config.type];
          newStatuses[config.type].unmappedCount = typeData?.total_records || 0;
        }
      });
      setUploadStatuses(newStatuses);

    } catch (error) {
      console.error('Error fetching unmapped summary:', error);
    }
  };

  const handleDataUpload = async (sensorType: SensorType, file: File) => {
    if (!file) return;

    setUploadStatuses(prev => ({
      ...prev,
      [sensorType]: { 
        ...prev[sensorType], 
        isUploading: true, 
        error: undefined 
      }
    }));

    try {
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
          lastUpload: result,
          error: undefined
        }
      }));

      alert(`${getSensorName(sensorType)}データのアップロードが完了しました。\n処理レコード数: ${result.processed_records}`);
      
      // サマリー再取得
      await fetchUnmappedSummary();

    } catch (error: any) {
      console.error('Upload error:', error);
      
      setUploadStatuses(prev => ({
        ...prev,
        [sensorType]: { 
          ...prev[sensorType], 
          isUploading: false,
          error: error.message || 'アップロードに失敗しました'
        }
      }));
      
      alert(`アップロードに失敗しました: ${error.message}`);
    }
  };

  const handleMappingUpload = async (sensorType: SensorType, mappingFile: File) => {
    if (!mappingFile) return;

    setUploadStatuses(prev => ({
      ...prev,
      [sensorType]: { 
        ...prev[sensorType], 
        isMapping: true, 
        error: undefined 
      }
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
          lastMapping: result,
          error: undefined
        }
      }));

      alert(`${getSensorName(sensorType)}のマッピングが完了しました。\nマッピング適用: ${result.mapped_records}件`);
      
      // サマリー再取得
      await fetchUnmappedSummary();

    } catch (error: any) {
      console.error('Mapping error:', error);
      
      setUploadStatuses(prev => ({
        ...prev,
        [sensorType]: { 
          ...prev[sensorType], 
          isMapping: false,
          error: error.message || 'マッピングに失敗しました'
        }
      }));
      
      alert(`マッピングに失敗しました: ${error.message}`);
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

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <LoadingSpinner size="lg" />
        <span className="ml-3 text-gray-600">データを読み込み中...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* ヘッダー */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">マルチセンサーデータアップロード</h1>
          <p className="text-gray-600 mt-1">センサー種別ごとにデータをアップロードし、後からマッピングを適用できます</p>
        </div>
        <Button onClick={fetchUnmappedSummary} variant="outline" size="sm">
          🔄 状況更新
        </Button>
      </div>

      {/* 大会選択 */}
      <Card className="p-6">
        <h2 className="text-lg font-semibold mb-4">🏆 大会選択</h2>
        <div className="flex gap-4 items-center">
          <select 
            value={selectedCompetition} 
            onChange={(e) => setSelectedCompetition(e.target.value)}
            className="flex-1 p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">大会を選択してください</option>
            {competitions.map(comp => (
              <option key={comp.competition_id} value={comp.competition_id}>
                {comp.name} ({comp.date ? new Date(comp.date).toLocaleDateString('ja-JP') : '日程未定'})
              </option>
            ))}
          </select>
          {selectedCompetition && (
            <div className="px-3 py-2 bg-blue-50 text-blue-700 rounded-md text-sm font-medium">
              選択中
            </div>
          )}
        </div>
        {!selectedCompetition && (
          <div className="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
            <p className="text-yellow-700 text-sm">⚠️ 大会を選択してください。選択しない場合、全大会共通データとして扱われます。</p>
          </div>
        )}
      </Card>

      {/* 未マッピングデータサマリー */}
      {unmappedSummary && unmappedSummary.total_unmapped_records > 0 && (
        <Card className="p-6 bg-gradient-to-r from-yellow-50 to-orange-50 border-yellow-200">
          <h2 className="text-lg font-semibold mb-4 text-yellow-800 flex items-center">
            ⚠️ 未マッピングデータ状況
            <span className="ml-2 bg-yellow-200 text-yellow-800 px-2 py-1 rounded-full text-sm">
              {unmappedSummary.total_unmapped_records}件
            </span>
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {SENSOR_CONFIGS.map(config => {
              const typeData = unmappedSummary.by_sensor_type?.[config.type];
              const count = typeData?.total_records || 0;
              
              return (
                <div key={config.type} className="text-center p-4 bg-white rounded-lg border shadow-sm">
                  <div className="text-3xl mb-2">{config.icon}</div>
                  <div className="text-2xl font-bold text-orange-600">
                    {count}
                  </div>
                  <div className="text-xs text-gray-600 font-medium">未マッピング</div>
                  <div className="text-xs text-gray-500 mt-1">
                    {typeData?.unique_sensors || 0} センサー
                  </div>
                  {count > 0 && (
                    <div className="mt-2 text-xs text-orange-600 font-medium">
                      マッピング必要
                    </div>
                  )}
                </div>
              );
            })}
          </div>
          <div className="mt-4 p-3 bg-yellow-100 rounded-md">
            <p className="text-yellow-800 text-sm font-medium">
              📝 未マッピングデータは被験者に表示されません。各センサーのマッピングファイルをアップロードしてください。
            </p>
          </div>
        </Card>
      )}

      {/* 進行状況インジケーター */}
      {unmappedSummary && (
        <Card className="p-4 bg-blue-50">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-blue-800">全体の進行状況</h3>
            <div className="text-sm text-blue-600">
              {unmappedSummary.total_unmapped_records === 0 ? '✅ 全データマッピング完了' : `${unmappedSummary.total_unmapped_records}件のマッピングが必要`}
            </div>
          </div>
        </Card>
      )}

      {/* センサー種別ごとのアップロードセクション */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {SENSOR_CONFIGS.map(config => (
          <SensorUploadCard
            key={config.type}
            config={config}
            status={uploadStatuses[config.type] || { isUploading: false, isMapping: false, unmappedCount: 0 }}
            onDataUpload={(file) => handleDataUpload(config.type, file)}
            onMappingUpload={(file) => handleMappingUpload(config.type, file)}
            selectedCompetition={selectedCompetition}
          />
        ))}
      </div>

      {/* 使用方法ガイド */}
      <Card className="p-6 bg-gray-50">
        <h2 className="text-lg font-semibold mb-4">📚 使用方法ガイド</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h3 className="font-medium text-gray-800 mb-2">🔄 処理フロー</h3>
            <ol className="text-sm text-gray-600 space-y-1">
              <li>1️⃣ 大会を選択</li>
              <li>2️⃣ センサーデータをアップロード（マッピング不要）</li>
              <li>3️⃣ マッピングファイルをアップロード（任意のタイミング）</li>
              <li>4️⃣ 被験者画面でデータ確認</li>
            </ol>
          </div>
          <div>
            <h3 className="font-medium text-gray-800 mb-2">💡 ポイント</h3>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• どの順番でアップロードしてもOK</li>
              <li>• データは失われません</li>
              <li>• マッピング前でも一時保存</li>
              <li>• 後からマッピング修正可能</li>
            </ul>
          </div>
        </div>
      </Card>
    </div>
  );
};

// === センサーアップロードカードコンポーネント ===

interface SensorUploadCardProps {
  config: SensorConfig;
  status: UploadStatus;
  onDataUpload: (file: File) => void;
  onMappingUpload: (file: File) => void;
  selectedCompetition: string;
}

const SensorUploadCard: React.FC<SensorUploadCardProps> = ({
  config,
  status,
  onDataUpload,
  onMappingUpload,
  selectedCompetition
}) => {
  const [dataFile, setDataFile] = useState<File | null>(null);
  const [mappingFile, setMappingFile] = useState<File | null>(null);
  const [showDataDetails, setShowDataDetails] = useState(false);
  const [showMappingDetails, setShowMappingDetails] = useState(false);

  const handleDataFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) setDataFile(file);
  };

  const handleMappingFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) setMappingFile(file);
  };

  const getCardBorderColor = () => {
    if (status.error) return 'border-red-300';
    if (status.unmappedCount > 0) return 'border-yellow-300';
    return 'border-gray-200';
  };

  const getHeaderColor = () => {
    if (status.error) return 'from-red-600 to-red-700';
    if (status.unmappedCount > 0) return 'from-yellow-600 to-orange-600';
    return 'from-blue-600 to-blue-700';
  };

  return (
    <Card className={`overflow-hidden ${getCardBorderColor()} transition-all duration-200`}>
      {/* ヘッダー */}
      <div className={`bg-gradient-to-r ${getHeaderColor()} px-6 py-4`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <span className="text-3xl mr-3">{config.icon}</span>
            <div>
              <h3 className="text-lg font-semibold text-white">{config.name}</h3>
              <p className="text-blue-100 text-sm">{config.description}</p>
            </div>
          </div>
          <div className="flex flex-col items-end gap-2">
            {status.unmappedCount > 0 && (
              <div className="bg-yellow-500 text-white px-3 py-1 rounded-full text-xs font-medium">
                {status.unmappedCount} 未マッピング
              </div>
            )}
            {status.lastUpload && (
              <div className="bg-green-500 text-white px-3 py-1 rounded-full text-xs font-medium">
                ✅ データ保存済み
              </div>
            )}
            {status.lastMapping && (
              <div className="bg-blue-500 text-white px-3 py-1 rounded-full text-xs font-medium">
                🔗 マッピング済み
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* エラー表示 */}
        {status.error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-red-700 text-sm font-medium">❌ エラー: {status.error}</p>
          </div>
        )}

        {/* データファイルアップロード */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <label className="block text-sm font-medium text-gray-700">
              📊 センサーデータファイル (CSV)
            </label>
            <Button
              onClick={() => setShowDataDetails(!showDataDetails)}
              variant="outline"
              size="sm"
              className="text-xs"
            >
              {showDataDetails ? '🔼 形式を隠す' : '🔽 形式を表示'}
            </Button>
          </div>
          
          <div className="flex gap-3">
            <input
              type="file"
              accept=".csv"
              onChange={handleDataFileChange}
              className="flex-1 text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
            />
            <Button
              onClick={() => dataFile && onDataUpload(dataFile)}
              disabled={!dataFile || status.isUploading || !selectedCompetition}
              size="sm"
              className="min-w-[100px]"
            >
              {status.isUploading ? <LoadingSpinner size="sm" /> : 'アップロード'}
            </Button>
          </div>

          {!selectedCompetition && (
            <p className="text-yellow-600 text-xs">⚠️ 大会を選択してください</p>
          )}

          {status.lastUpload && (
            <div className="text-sm text-green-600 bg-green-50 p-2 rounded">
              ✅ 最終アップロード: {status.lastUpload.processed_records}件処理完了
              {status.lastUpload.errors?.length > 0 && (
                <div className="text-orange-600 mt-1">
                  ⚠️ {status.lastUpload.errors.length}件のエラーがありました
                </div>
              )}
            </div>
          )}

          {showDataDetails && (
            <div className="mt-3 p-4 bg-gray-50 rounded-md text-sm border">
              <div className="font-medium text-gray-700 mb-2">📝 必須列:</div>
              <div className="font-mono text-xs bg-white p-2 rounded border mb-3">
                {config.csvFormat.join(', ')}
              </div>
              <div className="font-medium text-gray-700 mb-2">💡 例:</div>
              <div className="font-mono text-xs bg-white p-2 rounded border text-green-600 mb-3">
                {config.example}
              </div>
              <div className="text-xs text-gray-600 space-y-1">
                <div>• (optional) の列は省略可能です</div>
                <div>• timestamp形式: YYYY-MM-DD HH:MM:SS</div>
                <div>• ファイルサイズ上限: 10MB</div>
              </div>
            </div>
          )}
        </div>

        {/* マッピングファイルアップロード */}
        {config.type !== SensorType.WBGT && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="block text-sm font-medium text-gray-700">
                🔗 マッピングファイル (CSV)
              </label>
              <Button
                onClick={() => setShowMappingDetails(!showMappingDetails)}
                variant="outline"
                size="sm"
                className="text-xs"
              >
                {showMappingDetails ? '🔼 形式を隠す' : '🔽 形式を表示'}
              </Button>
            </div>

            <div className="flex gap-3">
              <input
                type="file"
                accept=".csv"
                onChange={handleMappingFileChange}
                className="flex-1 text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-medium file:bg-green-50 file:text-green-700 hover:file:bg-green-100"
              />
              <Button
                onClick={() => mappingFile && onMappingUpload(mappingFile)}
                disabled={!mappingFile || status.isMapping || status.unmappedCount === 0 || !selectedCompetition}
                size="sm"
                variant="outline"
                className="min-w-[100px]"
              >
                {status.isMapping ? <LoadingSpinner size="sm" /> : 'マッピング適用'}
              </Button>
            </div>

            {status.unmappedCount === 0 && (
              <p className="text-gray-500 text-xs">ℹ️ 未マッピングデータがありません</p>
            )}

            {status.lastMapping && (
              <div className="text-sm text-green-600 bg-green-50 p-2 rounded">
                ✅ 最終マッピング: {status.lastMapping.mapped_records}件適用完了
                {status.lastMapping.mapping_errors?.length > 0 && (
                  <div className="text-orange-600 mt-1">
                    ⚠️ {status.lastMapping.mapping_errors.length}件のエラーがありました
                  </div>
                )}
              </div>
            )}

            {showMappingDetails && (
              <div className="mt-3 p-4 bg-gray-50 rounded-md text-sm border">