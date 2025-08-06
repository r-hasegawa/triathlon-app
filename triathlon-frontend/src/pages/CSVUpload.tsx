import React, { useState } from 'react';
import { Layout } from '@/components/layout/Layout';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { FileDropzone } from '@/components/admin/FileDropzone';
import { UploadProgress } from '@/components/admin/UploadProgress';
import { UploadResults } from '@/components/admin/UploadResults';
import { adminService, UploadResponse } from '@/services/adminService';

export const CSVUpload: React.FC = () => {
  const [sensorDataFile, setSensorDataFile] = useState<File | null>(null);
  const [mappingFile, setMappingFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadResults, setUploadResults] = useState<UploadResponse | null>(null);
  const [errors, setErrors] = useState<{ [key: string]: string }>({});

  const validateFiles = () => {
    const newErrors: { [key: string]: string } = {};

    if (!sensorDataFile) {
      newErrors.sensorData = 'センサデータファイルを選択してください';
    }

    if (!mappingFile) {
      newErrors.mapping = 'マッピングファイルを選択してください';
    }

    // ファイルサイズチェック（10MB制限）
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (sensorDataFile && sensorDataFile.size > maxSize) {
      newErrors.sensorData = 'ファイルサイズが10MBを超えています';
    }

    if (mappingFile && mappingFile.size > maxSize) {
      newErrors.mapping = 'ファイルサイズが10MBを超えています';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleUpload = async () => {
    if (!validateFiles() || !sensorDataFile || !mappingFile) {
      return;
    }

    setIsUploading(true);
    setUploadResults(null);
    setErrors({});

    try {
      const results = await adminService.uploadCSVFiles(sensorDataFile, mappingFile);
      setUploadResults(results);
    } catch (error: any) {
      console.error('Upload error:', error);
      setErrors({
        upload: error.response?.data?.detail || 'アップロードに失敗しました。ファイル形式と内容を確認してください。'
      });
    } finally {
      setIsUploading(false);
    }
  };

  const resetForm = () => {
    setSensorDataFile(null);
    setMappingFile(null);
    setUploadResults(null);
    setErrors({});
  };

  return (
    <Layout>
      <div className="max-w-4xl mx-auto space-y-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">CSVファイルアップロード</h1>
          <p className="mt-1 text-sm text-gray-500">
            センサデータとセンサマッピングファイルを同時にアップロードできます
          </p>
        </div>

        {uploadResults ? (
          <UploadResults results={uploadResults} onClose={resetForm} />
        ) : (
          <>
            <UploadProgress isUploading={isUploading} status="ファイルを処理しています..." />

            <Card title="ファイル選択">
              <div className="space-y-6">
                <FileDropzone
                  onFileSelect={setSensorDataFile}
                  acceptedFile={sensorDataFile}
                  label="センサデータファイル"
                  description="sensor_id, timestamp, temperature の列を含むCSVファイル"
                  error={errors.sensorData}
                  disabled={isUploading}
                />

                <FileDropzone
                  onFileSelect={setMappingFile}
                  acceptedFile={mappingFile}
                  label="センサマッピングファイル"
                  description="sensor_id, user_id, subject_name の列を含むCSVファイル"
                  error={errors.mapping}
                  disabled={isUploading}
                />

                {errors.upload && (
                  <div className="bg-red-50 border border-red-200 rounded-md p-4">
                    <p className="text-sm text-red-600">{errors.upload}</p>
                  </div>
                )}

                <div className="flex justify-between items-center pt-4 border-t">
                  <div className="text-sm text-gray-500">
                    {sensorDataFile && mappingFile && (
                      <p>
                        ファイル準備完了 • 
                        総サイズ: {((sensorDataFile.size + mappingFile.size) / 1024).toFixed(1)} KB
                      </p>
                    )}
                  </div>
                  
                  <div className="flex space-x-3">
                    <Button
                      variant="outline"
                      onClick={resetForm}
                      disabled={isUploading}
                    >
                      リセット
                    </Button>
                    
                    <Button
                      onClick={handleUpload}
                      disabled={isUploading || !sensorDataFile || !mappingFile}
                      isLoading={isUploading}
                    >
                      {isUploading ? 'アップロード中...' : 'アップロード開始'}
                    </Button>
                  </div>
                </div>
              </div>
            </Card>

            {/* サンプルファイル情報 */}
            <Card title="CSVファイル形式について">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">センサデータCSV</h4>
                  <div className="bg-gray-50 p-3 rounded-md font-mono text-xs">
                    <div className="text-gray-600">sensor_id,timestamp,temperature</div>
                    <div>SENSOR_001,2025-01-01 09:00:00,36.5</div>
                    <div>SENSOR_001,2025-01-01 09:05:00,36.8</div>
                    <div>SENSOR_002,2025-01-01 09:00:00,37.2</div>
                  </div>
                </div>
                
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">センサマッピングCSV</h4>
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
                  💡 <strong>ヒント:</strong> サンプルファイルは uploads/csv/ フォルダにあります。
                  参考にしてテスト用ファイルを作成してください。
                </p>
              </div>
            </Card>
          </>
        )}
      </div>
    </Layout>
  );
};