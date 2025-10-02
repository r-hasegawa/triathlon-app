// triathlon-frontend/src/pages/SensorDataUpload/components/UploadHistoryTable.tsx

import React from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { UploadBatch } from '../index';

interface UploadHistoryTableProps {
  batches: UploadBatch[];
  onDelete: (batchId: string) => void;
  onRefresh: () => void;
}

const UploadHistoryTable: React.FC<UploadHistoryTableProps> = ({
  batches,
  onDelete,
  onRefresh
}) => {
  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold">アップロード履歴</h2>
        <Button onClick={onRefresh} variant="outline" size="sm">
          更新
        </Button>
      </div>
      
      {batches.length === 0 ? (
        <p className="text-gray-500 text-center py-8">アップロード履歴がありません</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-2 text-left">データ種別</th>
                <th className="px-4 py-2 text-left">ファイル名</th>
                <th className="px-4 py-2 text-center">総件数</th>
                <th className="px-4 py-2 text-center">成功</th>
                <th className="px-4 py-2 text-center">失敗</th>
                <th className="px-4 py-2 text-left">アップロード日時</th>
                <th className="px-4 py-2 text-center">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {batches.map((batch) => (
                <tr key={batch.batch_id} className="hover:bg-gray-50">
                  <td className="px-4 py-2">
                    <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">
                      {batch.sensor_type}
                    </span>
                  </td>
                  <td className="px-4 py-2">{batch.file_name}</td>
                  <td className="px-4 py-2 text-center">{batch.total_records}</td>
                  <td className="px-4 py-2 text-center text-green-600">{batch.success_records}</td>
                  <td className="px-4 py-2 text-center text-red-600">{batch.failed_records}</td>
                  <td className="px-4 py-2">
                    {new Date(batch.uploaded_at).toLocaleString('ja-JP')}
                  </td>
                  <td className="px-4 py-2 text-center">
                    <Button
                      onClick={() => onDelete(batch.batch_id)}
                      variant="outline"
                      size="sm"
                      className="text-red-600 hover:bg-red-50"
                    >
                      削除
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
};

export default UploadHistoryTable;