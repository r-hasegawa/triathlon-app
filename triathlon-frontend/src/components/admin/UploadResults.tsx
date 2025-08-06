import React from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { UploadResponse } from '@/services/adminService';

interface UploadResultsProps {
  results: UploadResponse;
  onClose: () => void;
}

export const UploadResults: React.FC<UploadResultsProps> = ({ results, onClose }) => {
  const hasErrors = results.sensor_data.total_errors > 0 || results.sensor_mapping.total_errors > 0;

  return (
    <Card className={`border-l-4 ${hasErrors ? 'border-l-yellow-500' : 'border-l-green-500'}`}>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h3 className={`text-lg font-medium ${hasErrors ? 'text-yellow-800' : 'text-green-800'}`}>
            {hasErrors ? 'アップロード完了（警告あり）' : 'アップロード完了'}
          </h3>
          <Button variant="outline" size="sm" onClick={onClose}>
            閉じる
          </Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* センサデータ結果 */}
          <div className="bg-blue-50 p-4 rounded-lg">
            <h4 className="font-medium text-blue-900 mb-2">センサデータ</h4>
            <div className="space-y-1 text-sm">
              <p className="text-blue-800">
                ✅ 処理済み: <span className="font-medium">{results.sensor_data.processed_records}件</span>
              </p>
              {results.sensor_data.total_errors > 0 && (
                <p className="text-red-600">
                  ⚠️ エラー: <span className="font-medium">{results.sensor_data.total_errors}件</span>
                </p>
              )}
              <p className="text-xs text-blue-600">
                ID: {results.upload_ids.sensor_data}
              </p>
            </div>

            {results.sensor_data.errors.length > 0 && (
              <details className="mt-2">
                <summary className="text-xs text-red-600 cursor-pointer">エラー詳細を表示</summary>
                <div className="mt-1 bg-white rounded p-2 text-xs text-red-600 max-h-32 overflow-y-auto">
                  {results.sensor_data.errors.map((error, index) => (
                    <p key={index}>{error}</p>
                  ))}
                </div>
              </details>
            )}
          </div>

          {/* マッピング結果 */}
          <div className="bg-green-50 p-4 rounded-lg">
            <h4 className="font-medium text-green-900 mb-2">センサマッピング</h4>
            <div className="space-y-1 text-sm">
              <p className="text-green-800">
                ✅ 処理済み: <span className="font-medium">{results.sensor_mapping.processed_records}件</span>
              </p>
              {results.sensor_mapping.total_errors > 0 && (
                <p className="text-red-600">
                  ⚠️ エラー: <span className="font-medium">{results.sensor_mapping.total_errors}件</span>
                </p>
              )}
              <p className="text-xs text-green-600">
                ID: {results.upload_ids.sensor_mapping}
              </p>
            </div>

            {results.sensor_mapping.errors.length > 0 && (
              <details className="mt-2">
                <summary className="text-xs text-red-600 cursor-pointer">エラー詳細を表示</summary>
                <div className="mt-1 bg-white rounded p-2 text-xs text-red-600 max-h-32 overflow-y-auto">
                  {results.sensor_mapping.errors.map((error, index) => (
                    <p key={index}>{error}</p>
                  ))}
                </div>
              </details>
            )}
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
  );
};