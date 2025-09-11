import React, { useState, useEffect } from 'react';
import { Layout } from '@/components/layout/Layout';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { useAuth } from '@/contexts/AuthContext';

interface DataSummary {
  total_sensor_records: number;
  mapped_records: number;
  unmapped_records: number;
  sensor_type_counts: Record<string, number>;
  wbgt_records: number;
  mapping_records: number;
  competition_id: string | null;
}

interface MappingStatus {
  status_counts: Record<string, number>;
  unmapped_by_sensor_type: Record<string, number>;
  competition_id: string | null;
}

export const MultiSensorStatus: React.FC = () => {
  const { token } = useAuth();
  const [competitionId, setCompetitionId] = useState('');
  const [dataSummary, setDataSummary] = useState<DataSummary | null>(null);
  const [mappingStatus, setMappingStatus] = useState<MappingStatus | null>(null);
  const [unmappedSensors, setUnmappedSensors] = useState<Record<string, string[]>>({});
  const [isLoading, setIsLoading] = useState(false);

  const fetchDataSummary = async () => {
    setIsLoading(true);
    try {
      const params = new URLSearchParams();
      if (competitionId) params.append('competition_id', competitionId);

      const response = await fetch(`/api/multi-sensor/status?${params}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setDataSummary(data);
      }
    } catch (error) {
      console.error('Failed to fetch data summary:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchMappingStatus = async () => {
    try {
      const params = new URLSearchParams();
      if (competitionId) params.append('competition_id', competitionId);

      const response = await fetch(`/api/multi-sensor/mapping-status?${params}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setMappingStatus(data);
      }
    } catch (error) {
      console.error('Failed to fetch mapping status:', error);
    }
  };

  const fetchUnmappedSensors = async () => {
    try {
      const params = new URLSearchParams();
      if (competitionId) params.append('competition_id', competitionId);

      const response = await fetch(`/api/multi-sensor/unmapped-sensors?${params}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setUnmappedSensors(data);
      }
    } catch (error) {
      console.error('Failed to fetch unmapped sensors:', error);
    }
  };

  const loadAllData = () => {
    fetchDataSummary();
    fetchMappingStatus();
    fetchUnmappedSensors();
  };

  useEffect(() => {
    loadAllData();
  }, []);

  const sensorTypeLabels: Record<string, string> = {
    'skin_temperature': '体表温度',
    'core_temperature': 'カプセル体温',
    'heart_rate': '心拍数',
    'wbgt': 'WBGT',
    'other': 'その他'
  };

  const statusLabels: Record<string, string> = {
    'unmapped': '未マッピング',
    'mapped': 'マッピング済み',
    'invalid': '無効なマッピング',
    'archived': 'アーカイブ済み'
  };

  return (
    <Layout>
      <div className="max-w-6xl mx-auto p-6 space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-gray-900">マルチセンサーデータ状況</h1>
          <Button onClick={loadAllData} disabled={isLoading}>
            {isLoading ? (
              <>
                <LoadingSpinner size="sm" />
                <span className="ml-2">読み込み中...</span>
              </>
            ) : '更新'}
          </Button>
        </div>

        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">検索条件</h2>
          <div className="flex gap-4 items-end">
            <div className="flex-1 max-w-md">
              <Input
                label="大会ID"
                value={competitionId}
                onChange={(e) => setCompetitionId(e.target.value)}
                placeholder="特定の大会のみ表示する場合は入力"
              />
            </div>
            <Button onClick={loadAllData} disabled={isLoading}>
              絞り込み検索
            </Button>
          </div>
        </Card>

        {dataSummary && (
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">データサマリー</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">
                  {dataSummary.total_sensor_records.toLocaleString()}
                </div>
                <div className="text-sm text-blue-800">総センサーレコード</div>
              </div>
              
              <div className="bg-green-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-green-600">
                  {dataSummary.mapped_records.toLocaleString()}
                </div>
                <div className="text-sm text-green-800">マッピング済み</div>
              </div>
              
              <div className="bg-yellow-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-yellow-600">
                  {dataSummary.unmapped_records.toLocaleString()}
                </div>
                <div className="text-sm text-yellow-800">未マッピング</div>
              </div>
              
              <div className="bg-purple-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-purple-600">
                  {dataSummary.wbgt_records.toLocaleString()}
                </div>
                <div className="text-sm text-purple-800">WBGTレコード</div>
              </div>
              
              <div className="bg-indigo-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-indigo-600">
                  {dataSummary.mapping_records.toLocaleString()}
                </div>
                <div className="text-sm text-indigo-800">マッピング設定</div>
              </div>
            </div>
            
            {dataSummary.competition_id && (
              <div className="mt-4 text-sm text-gray-600">
                対象大会: {dataSummary.competition_id}
              </div>
            )}
          </Card>
        )}

        {dataSummary && (
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">センサー種別ごとのデータ数</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {Object.entries(dataSummary.sensor_type_counts).map(([type, count]) => (
                <div key={type} className="border border-gray-200 p-4 rounded-lg">
                  <div className="text-lg font-semibold text-gray-900">
                    {count.toLocaleString()}
                  </div>
                  <div className="text-sm text-gray-600">
                    {sensorTypeLabels[type] || type}
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )}

        {mappingStatus && (
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">マッピング状況</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="text-lg font-medium mb-3">全体状況</h3>
                <div className="space-y-2">
                  {Object.entries(mappingStatus.status_counts).map(([status, count]) => (
                    <div key={status} className="flex justify-between items-center p-3 bg-gray-50 rounded">
                      <span className="text-sm font-medium">
                        {statusLabels[status] || status}
                      </span>
                      <span className="text-lg font-semibold">{count.toLocaleString()}</span>
                    </div>
                  ))}
                </div>
              </div>
              
              <div>
                <h3 className="text-lg font-medium mb-3">未マッピング（種別ごと）</h3>
                <div className="space-y-2">
                  {Object.entries(mappingStatus.unmapped_by_sensor_type).map(([type, count]) => (
                    <div key={type} className="flex justify-between items-center p-3 bg-yellow-50 rounded">
                      <span className="text-sm font-medium">
                        {sensorTypeLabels[type] || type}
                      </span>
                      <span className="text-lg font-semibold text-yellow-600">{count.toLocaleString()}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </Card>
        )}

        {Object.keys(unmappedSensors).length > 0 && (
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">未マッピングセンサー一覧</h2>
            <div className="space-y-6">
              {Object.entries(unmappedSensors).map(([type, sensors]) => (
                <div key={type}>
                  <h3 className="text-lg font-medium mb-3 text-gray-900">
                    {sensorTypeLabels[type] || type} ({sensors.length}個)
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-2">
                    {sensors.map((sensorId) => (
                      <div
                        key={sensorId}
                        className="px-3 py-2 bg-yellow-100 text-yellow-800 rounded text-sm font-mono"
                      >
                        {sensorId}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )}

        {!isLoading && dataSummary && dataSummary.total_sensor_records === 0 && (
          <Card className="p-6 text-center">
            <div className="text-gray-500">
              <div className="w-16 h-16 mx-auto mb-4 text-gray-300">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" 
                        d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <p className="text-lg mb-2">データが見つかりません</p>
              <p className="text-sm">
                {competitionId 
                  ? `大会ID「${competitionId}」のデータが存在しないか、まだアップロードされていません。`
                  : 'センサーデータがまだアップロードされていません。'
                }
              </p>
            </div>
          </Card>
        )}

        {isLoading && !dataSummary && (
          <Card className="p-6 text-center">
            <LoadingSpinner size="lg" text="データを読み込み中..." />
          </Card>
        )}
      </div>
    </Layout>
  );
};