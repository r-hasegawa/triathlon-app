import React, { useState, useEffect } from 'react';
import { Layout } from '@/components/layout/Layout';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { useAuth } from '@/contexts/AuthContext';

interface Competition {
  competition_id: string;
  name: string;
  date: string | null;
}

interface UploadResult {
  success: boolean;
  message: string;
  total_records: number;
  processed_records: number;
}

export const MultiSensorUpload: React.FC = () => {
  const { token } = useAuth();
  
  // State variables
  const [competitions, setCompetitions] = useState<Competition[]>([]);
  const [selectedCompetition, setSelectedCompetition] = useState('');
  const [selectedSensorType, setSelectedSensorType] = useState('');
  const [dataFiles, setDataFiles] = useState<FileList | null>(null);
  const [wbgtFile, setWbgtFile] = useState<File | null>(null);
  const [mappingFile, setMappingFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [competitionsLoading, setCompetitionsLoading] = useState(true);
  const [results, setResults] = useState<any[]>([]);

  // Load competitions on mount
  useEffect(() => {
    loadCompetitions();
  }, []);

  const loadCompetitions = async () => {
    try {
      setCompetitionsLoading(true);
      const response = await fetch('/api/competitions/', {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setCompetitions(data);
      }
    } catch (error) {
      console.error('Failed to load competitions:', error);
    } finally {
      setCompetitionsLoading(false);
    }
  };

  const uploadSensorData = async () => {
    if (!selectedCompetition) {
      alert('大会を選択してください');
      return;
    }
    if (!selectedSensorType) {
      alert('センサー種別を選択してください');
      return;
    }
    if (!dataFiles || dataFiles.length === 0) {
      alert('データファイルを選択してください');
      return;
    }

    setIsLoading(true);
    try {
      if (dataFiles.length === 1) {
        // Single file upload
        const formData = new FormData();
        formData.append('data_file', dataFiles[0]);
        formData.append('competition_id', selectedCompetition);

        const response = await fetch(`/api/multi-sensor/upload/${selectedSensorType}`, {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` },
          body: formData
        });

        const result = await response.json();
        setResults(prev => [...prev, { type: 'sensor', result }]);
      } else {
        // Multiple files upload
        const formData = new FormData();
        formData.append('sensor_type', selectedSensorType);
        formData.append('competition_id', selectedCompetition);
        Array.from(dataFiles).forEach(file => {
          formData.append('data_files', file);
        });

        const response = await fetch('/api/multi-sensor/upload/multiple-sensors', {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` },
          body: formData
        });

        const result = await response.json();
        setResults(prev => [...prev, { type: 'multiple', result }]);
      }
    } catch (error) {
      console.error('Upload error:', error);
      alert('アップロードに失敗しました');
    } finally {
      setIsLoading(false);
    }
  };

  const uploadWBGT = async () => {
    if (!selectedCompetition) {
      alert('大会を選択してください');
      return;
    }
    if (!wbgtFile) {
      alert('WBGTファイルを選択してください');
      return;
    }

    setIsLoading(true);
    try {
      const formData = new FormData();
      formData.append('data_file', wbgtFile);
      formData.append('competition_id', selectedCompetition);

      const response = await fetch('/api/multi-sensor/upload/wbgt', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData
      });

      const result = await response.json();
      setResults(prev => [...prev, { type: 'wbgt', result }]);
    } catch (error) {
      console.error('WBGT upload error:', error);
      alert('WBGTアップロードに失敗しました');
    } finally {
      setIsLoading(false);
    }
  };

  const uploadMapping = async () => {
    if (!selectedCompetition) {
      alert('大会を選択してください');
      return;
    }
    if (!mappingFile) {
      alert('マッピングファイルを選択してください');
      return;
    }

    setIsLoading(true);
    try {
      const formData = new FormData();
      formData.append('mapping_file', mappingFile);
      formData.append('competition_id', selectedCompetition);

      const response = await fetch('/api/multi-sensor/upload/mapping', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData
      });

      const result = await response.json();
      setResults(prev => [...prev, { type: 'mapping', result }]);
    } catch (error) {
      console.error('Mapping upload error:', error);
      alert('マッピングアップロードに失敗しました');
    } finally {
      setIsLoading(false);
    }
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '日程未定';
    return new Date(dateStr).toLocaleDateString('ja-JP');
  };

  return (
    <Layout>
      <div className="max-w-6xl mx-auto p-6 space-y-6">
        <h1 className="text-3xl font-bold text-gray-900">マルチセンサーデータ管理</h1>

        {/* Competition Selection */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">大会選択（必須）</h2>
          <div className="max-w-md">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              対象大会 <span className="text-red-500">*</span>
            </label>
            {competitionsLoading ? (
              <div className="flex items-center p-3 border rounded-md">
                <LoadingSpinner size="sm" />
                <span className="ml-2">大会一覧を読み込み中...</span>
              </div>
            ) : (
              <select
                value={selectedCompetition}
                onChange={(e) => setSelectedCompetition(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">大会を選択してください</option>
                {competitions.map(comp => (
                  <option key={comp.competition_id} value={comp.competition_id}>
                    {comp.name} ({formatDate(comp.date)})
                  </option>
                ))}
              </select>
            )}
          </div>
        </Card>

        {/* Sensor Data Upload */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">センサーデータアップロード</h2>
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  センサー種別
                </label>
                <select
                  value={selectedSensorType}
                  onChange={(e) => setSelectedSensorType(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">選択してください</option>
                  <option value="skin_temperature">体表温度（halshare）</option>
                  <option value="core_temperature">カプセル体温（e-Celcius）</option>
                  <option value="heart_rate">心拍数（Garmin）</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  データファイル（複数選択可）
                </label>
                <input
                  type="file"
                  multiple
                  accept=".csv"
                  onChange={(e) => setDataFiles(e.target.files)}
                  className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                />
                {dataFiles && (
                  <div className="mt-2 text-sm text-gray-600">
                    選択中: {dataFiles.length}ファイル
                  </div>
                )}
              </div>
            </div>
            
            <Button 
              onClick={uploadSensorData}
              disabled={isLoading || !selectedCompetition || !selectedSensorType || !dataFiles}
              className="w-full md:w-auto"
            >
              {isLoading ? (
                <>
                  <LoadingSpinner size="sm" />
                  <span className="ml-2">アップロード中...</span>
                </>
              ) : 'センサーデータをアップロード'}
            </Button>
          </div>
        </Card>

        {/* WBGT Upload */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">WBGT環境データアップロード</h2>
          <div className="space-y-4">
            <div className="max-w-md">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                WBGTデータファイル（1大会につき1ファイル、上書きされます）
              </label>
              <input
                type="file"
                accept=".csv"
                onChange={(e) => setWbgtFile(e.target.files?.[0] || null)}
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-medium file:bg-green-50 file:text-green-700 hover:file:bg-green-100"
              />
            </div>
            
            <Button 
              onClick={uploadWBGT}
              disabled={isLoading || !selectedCompetition || !wbgtFile}
              className="w-full md:w-auto bg-green-600 hover:bg-green-700"
            >
              {isLoading ? (
                <>
                  <LoadingSpinner size="sm" />
                  <span className="ml-2">アップロード中...</span>
                </>
              ) : 'WBGTデータをアップロード'}
            </Button>
          </div>
        </Card>

        {/* Mapping Upload */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">センサーマッピングデータアップロード</h2>
          <div className="space-y-4">
            <div className="max-w-md">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                マッピングファイル（1大会につき1ファイル、上書きされます）
              </label>
              <input
                type="file"
                accept=".csv"
                onChange={(e) => setMappingFile(e.target.files?.[0] || null)}
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-medium file:bg-purple-50 file:text-purple-700 hover:file:bg-purple-100"
              />
              <div className="mt-2 text-sm text-gray-500">
                形式: user_id, sensor1_id, sensor2_id... または ヘッダーなしCSV
              </div>
            </div>
            
            <Button 
              onClick={uploadMapping}
              disabled={isLoading || !selectedCompetition || !mappingFile}
              className="w-full md:w-auto bg-purple-600 hover:bg-purple-700"
            >
              {isLoading ? (
                <>
                  <LoadingSpinner size="sm" />
                  <span className="ml-2">アップロード中...</span>
                </>
              ) : 'マッピングデータをアップロード'}
            </Button>
          </div>
        </Card>

        {/* Results */}
        {results.length > 0 && (
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">アップロード結果</h2>
            <div className="space-y-4">
              {results.map((item, index) => (
                <div key={index} className="border rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <div className={`w-3 h-3 rounded-full ${item.result.success ? 'bg-green-500' : 'bg-red-500'}`} />
                    <span className="font-medium">
                      {item.type === 'sensor' && 'センサーデータアップロード'}
                      {item.type === 'multiple' && '複数ファイルアップロード'}
                      {item.type === 'wbgt' && 'WBGTデータアップロード'}
                      {item.type === 'mapping' && 'マッピングデータアップロード'}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600">{item.result.message}</p>
                  {item.result.processed_records && (
                    <p className="text-sm text-gray-500">
                      処理件数: {item.result.processed_records}
                      {item.result.total_records && `/${item.result.total_records}`}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </Card>
        )}
      </div>
    </Layout>
  );
};