import React from 'react';
import { Layout } from '@/components/layout/Layout';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { DataFilters } from '@/components/data/DataFilters';
import { SensorDataTable } from '@/components/data/SensorDataTable';
import { useDataDetail } from '@/hooks/useDataDetail';
import { dataService } from '@/services/dataService';

export const DataDetail: React.FC = () => {
  const {
    data,
    sensors,
    totalCount,
    pageIndex,
    pageSize,
    filters,
    isLoading,
    error,
    handleFiltersChange,
    handlePageChange,
    handlePageSizeChange,
    handleReset,
    refetch,
  } = useDataDetail();

  const handleExport = async (format: 'csv' | 'json') => {
    try {
      const blob = await dataService.exportData(format, filters);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `sensor_data_${new Date().toISOString().slice(0, 10)}.${format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      console.error('Export error:', err);
      alert('エクスポートに失敗しました');
    }
  };

  return (
    <Layout>
      <div className="space-y-6">
        {/* ヘッダー */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">データ詳細</h1>
            <p className="mt-1 text-sm text-gray-500">
              センサデータを詳細に確認・分析できます
            </p>
          </div>
          
          <div className="flex space-x-2">
            <Button
              variant="outline"
              onClick={() => handleExport('csv')}
              disabled={isLoading || totalCount === 0}
              size="sm"
            >
              📥 CSV出力
            </Button>
            
            <Button
              variant="outline"
              onClick={() => handleExport('json')}
              disabled={isLoading || totalCount === 0}
              size="sm"
            >
              📥 JSON出力
            </Button>
            
            <Button
              variant="outline"
              onClick={refetch}
              disabled={isLoading}
              size="sm"
            >
              🔄 更新
            </Button>
          </div>
        </div>

        {/* エラー表示 */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex justify-between items-center">
              <p className="text-sm text-red-600">{error}</p>
              <Button
                onClick={refetch}
                variant="outline"
                size="sm"
              >
                再試行
              </Button>
            </div>
          </div>
        )}

        {/* フィルター */}
        <DataFilters
          sensors={sensors}
          filters={filters}
          onFiltersChange={handleFiltersChange}
          onReset={handleReset}
          isLoading={isLoading}
        />

        {/* 統計サマリー */}
        {totalCount > 0 && (
          <Card>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="text-center">
                <p className="text-2xl font-bold text-blue-600">
                  {totalCount.toLocaleString()}
                </p>
                <p className="text-sm text-gray-500">総データ件数</p>
              </div>
              
              <div className="text-center">
                <p className="text-2xl font-bold text-green-600">
                  {data.length > 0 ? (
                    (data.reduce((sum, d) => sum + d.temperature, 0) / data.length).toFixed(1)
                  ) : '0.0'}°C
                </p>
                <p className="text-sm text-gray-500">表示中データの平均</p>
              </div>
              
              <div className="text-center">
                <p className="text-2xl font-bold text-red-600">
                  {data.length > 0 ? Math.max(...data.map(d => d.temperature)).toFixed(1) : '0.0'}°C
                </p>
                <p className="text-sm text-gray-500">表示中データの最高</p>
              </div>
              
              <div className="text-center">
                <p className="text-2xl font-bold text-blue-600">
                  {data.length > 0 ? Math.min(...data.map(d => d.temperature)).toFixed(1) : '0.0'}°C
                </p>
                <p className="text-sm text-gray-500">表示中データの最低</p>
              </div>
            </div>
          </Card>
        )}

        {/* データテーブル */}
        <SensorDataTable
          data={data}
          isLoading={isLoading}
          totalCount={totalCount}
          pageIndex={pageIndex}
          pageSize={pageSize}
          onPageChange={handlePageChange}
          onPageSizeChange={handlePageSizeChange}
        />

        {/* 使用方法のヒント */}
        {totalCount === 0 && !isLoading && !error && (
          <Card>
            <div className="text-center py-8 space-y-4">
              <div className="text-gray-400">
                <svg className="mx-auto h-16 w-16 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  データが見つかりませんでした
                </h3>
                
                <div className="text-sm text-gray-600 space-y-2">
                  <p>以下の点をご確認ください：</p>
                  <ul className="text-left list-disc list-inside space-y-1">
                    <li>センサデータがアップロードされているか</li>
                    <li>フィルター条件が適切に設定されているか</li>
                    <li>日付範囲にデータが存在するか</li>
                  </ul>
                </div>
                
                <div className="mt-4 flex justify-center space-x-2">
                  <Button
                    variant="outline"
                    onClick={handleReset}
                    size="sm"
                  >
                    フィルターをリセット
                  </Button>
                  
                  <Button
                    variant="outline"
                    onClick={() => window.location.href = '/dashboard'}
                    size="sm"
                  >
                    ダッシュボードに戻る
                  </Button>
                </div>
              </div>
            </div>
          </Card>
        )}
      </div>
    </Layout>
  );
};