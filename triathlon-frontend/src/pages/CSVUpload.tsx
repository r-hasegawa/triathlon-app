// src/pages/CSVUpload.tsx - 完全版
import React, { useState } from 'react';
import { Layout } from '@/components/layout/Layout';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { adminService, MultipleUploadResponse } from '@/services/adminService';

export const CSVUpload: React.FC = () => {
  const [sensorDataFiles, setSensorDataFiles] = useState<File[]>([]);
  const [sensorMappingFile, setSensorMappingFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<MultipleUploadResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // データファイル追加
  const handleSensorDataFileAdd = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []);
    setSensorDataFiles(prev => [...prev, ...files]);
    event.target.value = '';
  };

  // データファイル削除
  const removeSensorDataFile = (index: number) => {
    setSensorDataFiles(prev => prev.filter((_, i) => i !== index));
  };

  // マッピングファイル設定
  const handleSensorMappingFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    setSensorMappingFile(file || null);
  };

  // アップロード実行
  const handleUpload = async () => {
    if (sensorDataFiles.length === 0) {
      setError('最低1つのセンサデータファイルを選択してください');
      return;
    }

    if (!sensorMappingFile) {
      setError('センサマッピングファイルを選択してください');
      return;
    }

    setUploading(true);
    setError(null);
    setUploadResult(null);

    try {
      const result = await adminService.uploadMultipleCSVFiles(sensorDataFiles, sensorMappingFile);
      setUploadResult(result);
      setSensorDataFiles([]);
      setSensorMappingFile(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'アップロードに失敗しました');
    } finally {
      setUploading(false);
    }
  };

  // ファイルサイズ表示
  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const resetForm = () => {
    setSensorDataFiles([]);
    setSensorMappingFile(null);
    setUploadResult(null);
    setError(null);
  };

  return (
    <Layout>
      <div className="max-w-4xl mx-auto space-y-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">CSVファイルアップロード</h1>
          <p className="mt-1 text-sm text-gray-500">
            センサデータファイル（複数可）とマッピングファイルを同時にアップロードできます
          </p>
        </div>

        {/* アップロード結果表示 */}
        {uploadResult && (
          <Card className={`border-l-4 ${uploadResult.summary.total_errors > 0 ? 'border-l-yellow-500' : 'border-l-green-500'}`}>
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h3 className={`text-lg font-medium ${uploadResult.summary.total_errors > 0 ? 'text-yellow-800' : 'text-green-800'}`}>
                  {uploadResult.summary.total_errors > 0 ? 'アップロード完了（警告あり）' : 'アップロード完了'}
                </h3>
                <Button variant="outline" size="sm" onClick={resetForm}>
                  閉じる
                </Button>
              </div>

              {/* サマリー */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-blue-50 p-3 rounded-lg">
                  <div className="text-sm text-blue-600">処理ファイル数</div>
                  <div className="text-lg font-bold text-blue-900">
                    {uploadResult.summary.total_files_processed}
                  </div>
                </div>
                <div className="bg-green-50 p-3 rounded-lg">
                  <div className="text-sm text-green-600">処理レコード数</div>
                  <div className="text-lg font-bold text-green-900">
                    {uploadResult.summary.total_records_processed.toLocaleString()}
                  </div>
                </div>
                <div className="bg-yellow-50 p-3 rounded-lg">
                  <div className="text-sm text-yellow-600">エラー数</div>
                  <div className="text-lg font-bold text-yellow-900">
                    {uploadResult.summary.total_errors}
                  </div>
                </div>
                <div className="bg-red-50 p-3 rounded-lg">
                  <div className="text-sm text-red-600">エラーファイル数</div>
                  <div className="text-lg font-bold text-red-900">
                    {uploadResult.summary.files_with_errors}
                  </div>
                </div>
              </div>

              {/* マッピングファイル結果 */}
              <div>
                <h4 className="font-medium text-gray-900 mb-2">マッピングファイル</h4>
                <div className="bg-gray-50 p-3 rounded-md">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">{uploadResult.mapping_file.filename}</span>
                    <span className="text-sm text-gray-600">
                      {uploadResult.mapping_file.records_processed}件処理
                    </span>
                  </div>
                  {uploadResult.mapping_file.errors.length > 0 && (
                    <details className="mt-2">
                      <summary className="text-xs text-red-600 cursor-pointer">エラー詳細を表示</summary>
                      <div className="mt-1 bg-white rounded p-2 text-xs text-red-600 max-h-32 overflow-y-auto">
                        {uploadResult.mapping_file.errors.map((error, i) => (
                          <p key={i}>{error}</p>
                        ))}
                      </div>
                    </details>
                  )}
                </div>
              </div>

              {/* データファイル結果 */}
              <div>
                <h4 className="font-medium text-gray-900 mb-2">データファイル</h4>
                <div className="space-y-2">
                  {uploadResult.data_files.map((file, index) => (
                    <div key={index} className="bg-gray-50 p-3 rounded-md">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          {file.errors.length === 0 ? (
                            <svg className="h-4 w-4 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                            </svg>
                          ) : (
                            <svg className="h-4 w-4 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                            </svg>
                          )}
                          <span className="text-sm font-medium">{file.filename}</span>
                        </div>
                        <span className="text-sm text-gray-600">
                          {file.records_processed.toLocaleString()}件処理
                        </span>
                      </div>
                      {file.errors.length > 0 && (
                        <details className="mt-2">
                          <summary className="text-xs text-red-600 cursor-pointer">エラー詳細を表示</summary>
                          <div className="mt-1 bg-white rounded p-2 text-xs text-red-600 max-h-32 overflow-y-auto">
                            {file.errors.slice(0, 3).map((error, i) => (
                              <p key={i}>{error}</p>
                            ))}
                            {file.errors.length > 3 && (
                              <div className="text-gray-500">...他 {file.errors.length - 3} 件</div>
                            )}
                          </div>
                        </details>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-gray-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600">
                  💡 <strong>次の手順:</strong> データが正常にアップロードされました。
                  被験者はダッシュボードでデータを確認できるようになります。
                </p>
              </div>
            </div>
          </Card>
        )}

        {/* エラー表示 */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex">
              <svg className="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">エラー</h3>
                <div className="mt-1 text-sm text-red-700">{error}</div>
              </div>
            </div>
          </div>
        )}

        {/* アップロードフォーム */}
        {!uploadResult && (
          <Card title="ファイル選択">
            <div className="space-y-6">
              {/* センサデータファイル（複数） */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  センサデータCSVファイル（複数選択可能）
                </label>
                
                {/* 選択済みファイル一覧 */}
                {sensorDataFiles.length > 0 && (
                  <div className="mb-4 space-y-2">
                    {sensorDataFiles.map((file, index) => (
                      <div key={index} className="flex items-center justify-between bg-gray-50 p-3 rounded-md">
                        <div className="flex items-center space-x-3">
                          <svg className="h-5 w-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                          </svg>
                          <div>
                            <span className="text-sm font-medium text-gray-900">{file.name}</span>
                            <p className="text-xs text-gray-500">{formatFileSize(file.size)}</p>
                          </div>
                        </div>
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() => removeSensorDataFile(index)}
                          disabled={uploading}
                        >
                          削除
                        </Button>
                      </div>
                    ))}
                  </div>
                )}

                {/* ファイル追加ボタン */}
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                  <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                    <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                  <div className="mt-4">
                    <label className="cursor-pointer">
                      <span className="mt-2 block text-sm font-medium text-gray-900">
                        クリックしてファイルを選択
                      </span>
                      <input
                        type="file"
                        className="sr-only"
                        accept=".csv"
                        multiple
                        onChange={handleSensorDataFileAdd}
                        disabled={uploading}
                      />
                    </label>
                    <p className="mt-1 text-xs text-gray-500">CSV形式 (最大10MB/ファイル、複数選択可)</p>
                  </div>
                </div>
              </div>

              {/* センサマッピングファイル（単一） */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  センサマッピングCSVファイル
                </label>
                
                {sensorMappingFile ? (
                  <div className="bg-gray-50 p-3 rounded-md">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <svg className="h-5 w-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        <div>
                          <span className="text-sm font-medium text-gray-900">{sensorMappingFile.name}</span>
                          <p className="text-xs text-gray-500">{formatFileSize(sensorMappingFile.size)}</p>
                        </div>
                      </div>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => setSensorMappingFile(null)}
                        disabled={uploading}
                      >
                        削除
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                    <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                      <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                    <div className="mt-4">
                      <label className="cursor-pointer">
                        <span className="mt-2 block text-sm font-medium text-gray-900">
                          クリックしてファイルを選択
                        </span>
                        <input
                          type="file"
                          className="sr-only"
                          accept=".csv"
                          onChange={handleSensorMappingFileChange}
                          disabled={uploading}
                        />
                      </label>
                      <p className="mt-1 text-xs text-gray-500">CSV形式 (最大10MB)</p>
                    </div>
                  </div>
                )}
              </div>

              {/* アップロード状態表示 */}
              {uploading && (
                <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
                  <div className="flex items-center">
                    <div className="spinner h-5 w-5 mr-3" />
                    <div>
                      <h3 className="text-sm font-medium text-blue-800">アップロード中</h3>
                      <div className="mt-1 text-sm text-blue-700">ファイルを処理しています...</div>
                    </div>
                  </div>
                </div>
              )}

              <div className="flex justify-between items-center pt-4 border-t">
                <div className="text-sm text-gray-500">
                  {sensorDataFiles.length > 0 && sensorMappingFile && (
                    <p>
                      ファイル準備完了 • データファイル: {sensorDataFiles.length}個 • 
                      総サイズ: {((sensorDataFiles.reduce((sum, file) => sum + file.size, 0) + sensorMappingFile.size) / 1024).toFixed(1)} KB
                    </p>
                  )}
                </div>
                
                <div className="flex space-x-3">
                  <Button
                    variant="outline"
                    onClick={resetForm}
                    disabled={uploading}
                  >
                    リセット
                  </Button>
                  
                  <Button
                    onClick={handleUpload}
                    disabled={uploading || sensorDataFiles.length === 0 || !sensorMappingFile}
                    isLoading={uploading}
                  >
                    {uploading ? 'アップロード中...' : 'アップロード開始'}
                  </Button>
                </div>
              </div>
            </div>
          </Card>
        )}

        {/* 使用例 */}
        <Card title="CSVファイル形式について">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-medium text-gray-900 mb-2">センサデータCSV（複数ファイル可）</h4>
              <div className="bg-gray-50 p-3 rounded-md font-mono text-xs">
                <div className="text-gray-600">sensor_id,timestamp,temperature</div>
                <div>SENSOR_001,2025-01-01 09:00:00,36.5</div>
                <div>SENSOR_001,2025-01-01 09:05:00,36.8</div>
                <div>SENSOR_002,2025-01-01 09:00:00,37.2</div>
              </div>
            </div>
            
            <div>
              <h4 className="font-medium text-gray-900 mb-2">センサマッピングCSV（1ファイル）</h4>
              <div className="bg-gray-50 p-3 rounded-md font-mono text-xs">
                <div className="text-gray-600">sensor_id,user_id,subject_name</div>
                <div>SENSOR_001,user001,田中太郎</div>
                <div>SENSOR_002,user002,佐藤花子</div>
                <div>SENSOR_003,user003,山田次郎</div>
              </div>
            </div>
          </div>
          
          <div className="mt-4 p-3 bg-blue-50 rounded-md">
            <p className="text-sm text-blue-800">
              💡 <strong>ヒント:</strong> データファイルは複数選択可能です。
              同じセンサマッピングファイルを使用して、複数のデータファイルを一度に処理できます。
            </p>
          </div>
        </Card>
      </div>
    </Layout>
  );
};