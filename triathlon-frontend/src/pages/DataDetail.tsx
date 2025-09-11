import React from 'react';
import { useDataDetail } from '@/hooks/useDataDetail';
import { SensorDataTable } from '@/components/data/SensorDataTable';
import { DataFilters } from '@/components/data/DataFilters';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorMessage } from '@/components/ui/ErrorMessage';

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

  return (
    <div className="space-y-6">
      <div className="bg-white shadow rounded-lg p-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">
          センサーデータ詳細
        </h1>

        <DataFilters
          sensors={sensors}
          filters={filters}
          onFiltersChange={handleFiltersChange}
          onReset={handleReset}
        />
      </div>

      <div className="bg-white shadow rounded-lg p-6">
        {error && (
          <div className="mb-4">
            <ErrorMessage message={error} onRetry={refetch} />
          </div>
        )}

        {isLoading && !data.length ? (
          <div className="flex justify-center py-12">
            <LoadingSpinner size="lg" text="データを読み込んでいます..." />
          </div>
        ) : (
          <SensorDataTable
            data={data}
            isLoading={isLoading}
            totalCount={totalCount}
            pageIndex={pageIndex}
            pageSize={pageSize}
            onPageChange={handlePageChange}
            onPageSizeChange={handlePageSizeChange}
          />
        )}
      </div>
    </div>
  );
};