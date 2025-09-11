/**
 * MultiSensorUpload.tsx - エンドポイント規則対応版（完全版）
 */

import React, { useState, useEffect } from 'react';
import { Layout } from '@/components/layout/Layout';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

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
  filename: string;
  type: string;
  status: string;
}

export const MultiSensorUpload: React.FC = () => {
  const [competitions, setCompetitions] = useState<Competition[]>([]);
  const [selectedCompetition, setSelectedCompetition] = useState('');
  const [selectedSensorType, setSelectedSensorType] = useState('');
  const [dataFiles, setDataFiles] = useState<FileList | null>(null);
  const [wbgtFile, setWbgtFile] = useState<File | null>(null);
  const [mappingFile, setMappingFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [competitionsLoading, setCompetitionsLoading] = useState(true);
  const [results, setResults] = useState<UploadResult[]>([]);

  useEffect(() => {
    loadCompetitions();
  }, []);

  const loadCompetitions = async () => {
    try {
      setCompetitionsLoading(true);
      const token = localStorage.getItem('access_token');
      
      const response = await fetch('http://localhost:8000/admin/competitions', {
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setCompetitions(data);
      } else {
        console.error('Failed to load competitions:', response.status);
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
      alert('センサータイプを選択してください');
      return;
    }
    if (!dataFiles || dataFiles.length === 0) {
      alert('データファイルを選択してください');
      return;
    }

    setIsLoading(true);
    const uploadResults: UploadResult[] = [];

    try {
      for (let i = 0; i < dataFiles.length; i++) {
        const file = dataFiles[i];
        const formData = new FormData();
        formData.append('data_file', file);
        formData.append('competition_id', selectedCompetition);

        const token = localStorage.getItem('access_token');
        
        const response = await fetch(`http://localhost:8000/admin/multi-sensor/upload/${selectedSensorType}`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          },
          body: formData
        });

        const result = await response.json();
        uploadResults.push({
          filename: file.name,
          type: 'sensor',
          status: response.ok ? 'success' : 'error',
          success: response.ok,
          message: result.message || 'アップロード完了',
          total_records: result.total_records || 0,
          processed_records: result.processed_records || 0
        });
      }

      setResults(prev => [...prev, ...uploadResults]);
    } catch (error) {
      console.error('Upload failed:', error);
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

      const token = localStorage.getItem('access_token');
      
      const response = await fetch('http://localhost:8000/admin/multi-sensor/upload/wbgt', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      const result = await response.json();
      const uploadResult: UploadResult = {
        filename: wbgtFile.name,
        type: 'wbgt',
        status: response.ok ? 'success' : 'error',
        success: response.ok,
        message: result.message || 'WBGTアップロード完了',
        total_records: result.total_records || 0,
        processed_records: result.processed_records || 0
      };

      setResults(prev => [...prev, uploadResult]);
    } catch (error) {
      console.error('WBGT upload failed:', error);
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

      const token = localStorage.getItem('access_token');
      
      const response = await fetch('http://localhost:8000/admin/multi-sensor/mapping', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      const result = await response.json();
      const uploadResult: UploadResult = {
        filename: mappingFile.name,
        type: 'mapping',
        status: response.ok ? 'success' : 'error',
        success: response.ok,
        message: result.message || 'マッピングアップロード完了',
        total_records: result.total_records || 0,
        processed_records: result.processed_records || 0
      };

      setResults(prev => [...prev, uploadResult]);
    } catch (error) {
      console.error('Mapping upload failed:', error);
      alert('マッピングアップロードに失敗しました');
    } finally {
      setIsLoading(false);
    }
  };

  const clearResults = () => {
    setResults([]);
  };

  return (
    <Layout>
      <div className="space-y-8">
        {/* ヘッダー */}
        <div className="bg-gradient-to-r from-purple-600 to-purple-700 rounded-lg p-8">
          <h1 className="text-3xl font-bold text-white mb-2">マルチセンサーデータアップロード</h1>
          <p className="text-purple-100">
            体表温、コア体温、心拍、WBGT、マッピングデータを一括アップロード
          </p>
        </div>

        {/* 大会選択 */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">大会選択</h2>
          {competitionsLoading ? (
            <div className="flex items-center">
              <LoadingSpinner size="sm" />
              <span className="ml-2">大会データを読み込み中...</span>
            </div>
          ) : (
            <select
              value={selectedCompetition}
              onChange={(e) => setSelectedCompetition(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
            >
              <option value="">大会を選択してください</option>
              {competitions.map((comp) => (
                <option key={comp.competition_id} value={comp.competition_id}>
                  {comp.name} {comp.date && `(${new Date(comp.date).toLocaleDateString('ja-JP')})`}
                </option>
              ))}
            </select>
          )}
        </Card>

        {/* センサーデータアップロード */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">センサーデータアップロード</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                センサータイプ
              </label>
              <select
                value={selectedSensorType}
                onChange={(e) => setSelectedSensorType(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option value="">センサータイプを選択</option>
                <option value="skin-temperature">体表温</option>
                <option value="core-temperature">コア体温</option>
                <option value="heart-rate">心拍</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                データファイル (複数選択可能)
              </label>
              <input
                type="file"
                multiple
                accept=".csv"
                onChange={(e) => setDataFiles(e.target.files)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>

            <Button
              onClick={uploadSensorData}
              disabled={isLoading || !selectedCompetition || !selectedSensorType || !dataFiles}
              className="w-full"
            >
              {isLoading ? <LoadingSpinner size="sm" className="mr-2" /> : null}
              センサーデータアップロード
            </Button>
          </div>
        </Card>

        {/* WBGTデータアップロード */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">WBGT環境データアップロード</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                WBGTファイル
              </label>
              <input
                type="file"
                accept=".csv"
                onChange={(e) => setWbgtFile(e.target.files?.[0] || null)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>

            <Button
              onClick={uploadWBGT}
              disabled={isLoading || !selectedCompetition || !wbgtFile}
              className="w-full"
            >
              {isLoading ? <LoadingSpinner size="sm" className="mr-2" /> : null}
              WBGTデータアップロード
            </Button>
          </div>
        </Card>

        {/* マッピングデータアップロード */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">マッピングデータアップロード</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                マッピングファイル
              </label>
              <input
                type="file"
                accept=".csv"
                onChange={(e) => setMappingFile(e.target.files?.[0] || null)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>

            <Button
              onClick={uploadMapping}
              disabled={isLoading || !selectedCompetition || !mappingFile}
              className="w-full"
            >
              {isLoading ? <LoadingSpinner size="sm" className="mr-2" /> : null}
              マッピングデータアップロード
            </Button>
          </div>
        </Card>

        {/* アップロード結果 */}
        {results.length > 0 && (
          <Card className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-gray-900">アップロード結果</h2>
              <Button
                onClick={clearResults}
                variant="outline"
                size="sm"
              >
                結果をクリア
              </Button>
            </div>
            <div className="space-y-3">
              {results.map((result, index) => (
                <div
                  key={index}
                  className={`p-4 rounded-lg border-2 ${
                    result.status === 'success'
                      ? 'border-green-200 bg-green-50'
                      : 'border-red-200 bg-red-50'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <h4 className="font-medium text-gray-900 flex items-center gap-2">
                        {result.filename}
                        <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                          {result.type}
                        </span>
                      </h4>
                      <p className="text-sm text-gray-600 mt-1">{result.message}</p>
                      {result.processed_records > 0 && (
                        <p className="text-sm text-gray-600">
                          処理レコード数: {result.processed_records}/{result.total_records}
                        </p>
                      )}
                    </div>
                    <div className={`text-sm font-medium ${
                      result.status === 'success' ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {result.status === 'success' ? '✅ 成功' : '❌ 失敗'}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )}
      </div>
    </Layout>
  );
};