import React, { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { FilterOptions } from '@/components/data/DataFilters';
import { dataService } from '@/services/dataService';
import { SensorMapping } from '@/types/sensor';

interface ExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  sensors: SensorMapping[];
  currentFilters: FilterOptions;
  totalRecords: number;
}

export interface ExportOptions {
  format: 'csv' | 'json' | 'excel';
  dateRange: {
    start: string;
    end: string;
  };
  sensorIds: string[];
  includeHeaders: boolean;
  maxRecords: number;
  splitFiles: boolean;
  splitSize: number;
  includeMetadata: boolean;
  timezone: string;
  filename: string;
}

export const ExportModal: React.FC<ExportModalProps> = ({
  isOpen,
  onClose,
  sensors,
  currentFilters,
  totalRecords
}) => {
  const [exportOptions, setExportOptions] = useState<ExportOptions>({
    format: 'csv',
    dateRange: {
      start: currentFilters.start_date || new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().slice(0, 16),
      end: currentFilters.end_date || new Date().toISOString().slice(0, 16)
    },
    sensorIds: currentFilters.sensor_id ? [currentFilters.sensor_id] : [],
    includeHeaders: true,
    maxRecords: 10000,
    splitFiles: false,
    splitSize: 5000,
    includeMetadata: true,
    timezone: 'Asia/Tokyo',
    filename: `sensor_data_${new Date().toISOString().slice(0, 10)}`
  });

  const [isExporting, setIsExporting] = useState(false);
  const [exportProgress, setExportProgress] = useState(0);
  const [exportStatus, setExportStatus] = useState('');

  if (!isOpen) return null;

  const updateOption = <K extends keyof ExportOptions>(key: K, value: ExportOptions[K]) => {
    setExportOptions(prev => ({ ...prev, [key]: value }));
  };

  const updateDateRange = (key: 'start' | 'end', value: string) => {
    setExportOptions(prev => ({
      ...prev,
      dateRange: { ...prev.dateRange, [key]: value }
    }));
  };

  const toggleSensorId = (sensorId: string) => {
    setExportOptions(prev => ({
      ...prev,
      sensorIds: prev.sensorIds.includes(sensorId)
        ? prev.sensorIds.filter(id => id !== sensorId)
        : [...prev.sensorIds, sensorId]
    }));
  };

  const estimatedSize = () => {
    const recordCount = Math.min(exportOptions.maxRecords, totalRecords);
    const avgRecordSize = exportOptions.format === 'json' ? 120 : 50; // bytes
    const totalSize = recordCount * avgRecordSize;
    
    if (totalSize < 1024) return `${totalSize} B`;
    if (totalSize < 1024 * 1024) return `${(totalSize / 1024).toFixed(1)} KB`;
    return `${(totalSize / (1024 * 1024)).toFixed(1)} MB`;
  };

  const handleExport = async () => {
    setIsExporting(true);
    setExportProgress(0);
    setExportStatus('エクスポートを準備中...');

    try {
      const filters = {
        sensor_id: exportOptions.sensorIds.length > 0 ? exportOptions.sensorIds.join(',') : undefined,
        start_date: exportOptions.dateRange.start,
        end_date: exportOptions.dateRange.end,
        limit: exportOptions.maxRecords
      };

      if (exportOptions.splitFiles && exportOptions.maxRecords > exportOptions.splitSize) {
        // 分割エクスポート
        await handleSplitExport(filters);
      } else {
        // 通常のエクスポート
        await handleSingleExport(filters);
      }

      setExportStatus('エクスポート完了！');
      setTimeout(() => {
        onClose();
        setIsExporting(false);
        setExportProgress(0);
        setExportStatus('');
      }, 2000);

    } catch (error: any) {
      console.error('Export error:', error);
      setExportStatus(`エクスポートエラー: ${error.message}`);
      setIsExporting(false);
    }
  };

  const handleSingleExport = async (filters: any) => {
    setExportStatus('データをダウンロード中...');
    setExportProgress(50);

    const blob = await dataService.exportData(exportOptions.format, filters);
    
    setExportProgress(80);
    setExportStatus('ファイルを生成中...');

    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${exportOptions.filename}.${exportOptions.format}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);

    setExportProgress(100);
  };

  const handleSplitExport = async (filters: any) => {
    const totalRecords = exportOptions.maxRecords;
    const splitSize = exportOptions.splitSize;
    const totalFiles = Math.ceil(totalRecords / splitSize);

    for (let i = 0; i < totalFiles; i++) {
      const start = i * splitSize;
      const limit = Math.min(splitSize, totalRecords - start);
      
      setExportStatus(`ファイル ${i + 1}/${totalFiles} をダウンロード中...`);
      setExportProgress((i / totalFiles) * 90);

      const fileFilters = {
        ...filters,
        skip: start,
        limit: limit
      };

      const blob = await dataService.exportData(exportOptions.format, fileFilters);
      
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${exportOptions.filename}_part${i + 1}.${exportOptions.format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      // 少し間隔を空ける
      await new Promise(resolve => setTimeout(resolve, 500));
    }

    setExportProgress(100);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-90vh overflow-y-auto">
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-bold text-gray-900">データエクスポート</h2>
            <Button variant="outline" onClick={onClose} disabled={isExporting}>
              ✕
            </Button>
          </div>

          {isExporting ? (
            <div className="space-y-4">
              <div className="text-center">
                <LoadingSpinner size="lg" />
                <p className="mt-4 text-lg font-medium text-gray-900">{exportStatus}</p>
                <div className="mt-4 bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${exportProgress}%` }}
                  />
                </div>
                <p className="text-sm text-gray-500 mt-2">{exportProgress}% 完了</p>
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              {/* ファイル形式 */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  ファイル形式
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {(['csv', 'json', 'excel'] as const).map((format) => (
                    <button
                      key={format}
                      type="button"
                      onClick={() => updateOption('format', format)}
                      className={`px-4 py-2 rounded-md border text-sm font-medium ${
                        exportOptions.format === format
                          ? 'bg-blue-600 text-white border-blue-600'
                          : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                      }`}
                    >
                      {format.toUpperCase()}
                    </button>
                  ))}
                </div>
              </div>

              {/* 日付範囲 */}
              <div className="grid grid-cols-2 gap-4">
                <Input
                  label="開始日時"
                  type="datetime-local"
                  value={exportOptions.dateRange.start}
                  onChange={(e) => updateDateRange('start', e.target.value)}
                />
                <Input
                  label="終了日時"
                  type="datetime-local"
                  value={exportOptions.dateRange.end}
                  onChange={(e) => updateDateRange('end', e.target.value)}
                />
              </div>

              {/* センサー選択 */}
              {sensors.length > 1 && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    センサー選択
                  </label>
                  <div className="space-y-2 max-h-32 overflow-y-auto border rounded-md p-2">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={exportOptions.sensorIds.length === 0}
                        onChange={() => updateOption('sensorIds', [])}
                        className="mr-2"
                      />
                      全てのセンサー
                    </label>
                    {sensors.map((sensor) => (
                      <label key={sensor.sensor_id} className="flex items-center">
                        <input
                          type="checkbox"
                          checked={exportOptions.sensorIds.includes(sensor.sensor_id)}
                          onChange={() => toggleSensorId(sensor.sensor_id)}
                          className="mr-2"
                        />
                        {sensor.sensor_id} {sensor.subject_name && `(${sensor.subject_name})`}
                      </label>
                    ))}
                  </div>
                </div>
              )}

              {/* エクスポート設定 */}
              <div className="space-y-4">
                <Input
                  label="最大レコード数"
                  type="number"
                  value={exportOptions.maxRecords}
                  onChange={(e) => updateOption('maxRecords', parseInt(e.target.value))}
                  min="1"
                  max="100000"
                />

                <Input
                  label="ファイル名"
                  type="text"
                  value={exportOptions.filename}
                  onChange={(e) => updateOption('filename', e.target.value)}
                  placeholder="例: triathlon_data_2025"
                />

                {/* 分割エクスポート */}
                <div className="space-y-2">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={exportOptions.splitFiles}
                      onChange={(e) => updateOption('splitFiles', e.target.checked)}
                      className="mr-2"
                    />
                    大容量データを分割してエクスポート
                  </label>
                  
                  {exportOptions.splitFiles && (
                    <Input
                      label="分割サイズ（レコード数）"
                      type="number"
                      value={exportOptions.splitSize}
                      onChange={(e) => updateOption('splitSize', parseInt(e.target.value))}
                      min="1000"
                      max="10000"
                      className="ml-6"
                    />
                  )}
                </div>

                {/* その他のオプション */}
                <div className="space-y-2">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={exportOptions.includeHeaders}
                      onChange={(e) => updateOption('includeHeaders', e.target.checked)}
                      className="mr-2"
                    />
                    ヘッダー行を含める
                  </label>
                  
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={exportOptions.includeMetadata}
                      onChange={(e) => updateOption('includeMetadata', e.target.checked)}
                      className="mr-2"
                    />
                    メタデータを含める（エクスポート日時、条件など）
                  </label>
                </div>
              </div>

              {/* 推定ファイルサイズ */}
              <div className="bg-blue-50 p-4 rounded-lg">
                <h4 className="font-medium text-blue-900 mb-2">エクスポート概要</h4>
                <div className="text-sm text-blue-800 space-y-1">
                  <p>推定レコード数: {Math.min(exportOptions.maxRecords, totalRecords).toLocaleString()}件</p>
                  <p>推定ファイルサイズ: {estimatedSize()}</p>
                  {exportOptions.splitFiles && (
                    <p>分割ファイル数: {Math.ceil(exportOptions.maxRecords / exportOptions.splitSize)}個</p>
                  )}
                </div>
              </div>

              {/* アクションボタン */}
              <div className="flex justify-end space-x-3 pt-4 border-t">
                <Button
                  variant="outline"
                  onClick={onClose}
                >
                  キャンセル
                </Button>
                
                <Button
                  onClick={handleExport}
                  disabled={isExporting}
                >
                  エクスポート開始
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};