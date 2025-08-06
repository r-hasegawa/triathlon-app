import React, { useState, useEffect } from 'react';
import { Layout } from '@/components/layout/Layout';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { adminService, UploadHistory as UploadHistoryType } from '@/services/adminService';

export const UploadHistory: React.FC = () => {
  const [history, setHistory] = useState<UploadHistoryType[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      setIsLoading(true);
      setError('');
      const data = await adminService.getUploadHistory(0, 100);
      setHistory(data);
    } catch (err: any) {
      console.error('Error fetching upload history:', err);
      setError('履歴の取得に失敗しました');
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusBadge = (status: UploadHistoryType['status']) => {
    const statusConfig = {
      pending: { color: 'bg-yellow-100 text-yellow-800', label: '待機中' },
      processing: { color: 'bg-blue-100 text-blue-800', label: '処理中' },
      completed: { color: 'bg-green-100 text-green-800', label: '完了' },
      completed_with_errors: { color: 'bg-orange-100 text-orange-800', label: '完了（警告）' },
      failed: { color: 'bg-red-100 text-red-800', label: '失敗' }
    };

    const config = statusConfig[status] || statusConfig.pending;

    return (
      <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${config.color}`}>
        {config.label}
      </span>
    );
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (isLoading) {
    return (
      <Layout>
        <div className="flex justify-center items-center h-64">
          <LoadingSpinner size="lg" />
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-8">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">アップロード履歴</h1>
            <p className="mt-1 text-sm text-gray-500">
              過去のCSVアップロード履歴を確認できます
            </p>
          </div>
          
          <Button onClick={fetchHistory} variant="outline" size="sm">
            更新
          </Button>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        <Card>
          {history.length === 0 ? (
            <div className="text-center py-12">
              <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <h3 className="mt-2 text-sm font-medium text-gray-900">アップロード履歴がありません</h3>
              <p className="mt-1 text-sm text-gray-500">CSVファイルをアップロードすると履歴が表示されます</p>
            </div>
          ) : (
            <div className="overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      ファイル名
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      ステータス
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      処理件数
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      ファイルサイズ
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      アップロード日時
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      処理完了日時
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {history.map((item) => (
                    <tr key={item.upload_id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            {item.filename}
                          </div>
                          <div className="text-xs text-gray-500">
                            ID: {item.upload_id}
                          </div>
                        </div>
                      </td>
                      
                      <td className="px-6 py-4 whitespace-nowrap">
                        {getStatusBadge(item.status)}
                        {item.error_message && (
                          <details className="mt-1">
                            <summary className="text-xs text-red-600 cursor-pointer">
                              エラー詳細
                            </summary>
                            <div className="text-xs text-red-600 mt-1 p-2 bg-red-50 rounded">
                              {item.error_message}
                            </div>
                          </details>
                        )}
                      </td>
                      
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(item.uploaded_at).toLocaleString('ja-JP')}
                      </td>
                      
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {item.processed_at ? (
                          new Date(item.processed_at).toLocaleString('ja-JP')
                        ) : (
                          <span className="text-gray-400">未処理</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>

        {/* 統計情報 */}
        {history.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <div className="text-center">
                <p className="text-2xl font-bold text-blue-600">
                  {history.length}
                </p>
                <p className="text-sm text-gray-500">総アップロード数</p>
              </div>
            </Card>
            
            <Card>
              <div className="text-center">
                <p className="text-2xl font-bold text-green-600">
                  {history.filter(h => h.status === 'completed').length}
                </p>
                <p className="text-sm text-gray-500">成功</p>
              </div>
            </Card>
            
            <Card>
              <div className="text-center">
                <p className="text-2xl font-bold text-orange-600">
                  {history.filter(h => h.status === 'completed_with_errors').length}
                </p>
                <p className="text-sm text-gray-500">警告あり</p>
              </div>
            </Card>
            
            <Card>
              <div className="text-center">
                <p className="text-2xl font-bold text-red-600">
                  {history.filter(h => h.status === 'failed').length}
                </p>
                <p className="text-sm text-gray-500">失敗</p>
              </div>
            </Card>
          </div>
        )}
      </div>
    </Layout>
  );
};