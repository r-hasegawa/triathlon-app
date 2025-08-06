// src/components/data/DataFilters.tsx
import React, { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card } from '@/components/ui/Card';
import { SensorMapping } from '@/types/sensor';

export interface FilterOptions {
  sensor_id?: string;
  start_date?: string;
  end_date?: string;
  min_temperature?: number;
  max_temperature?: number;
  search?: string;
}

interface DataFiltersProps {
  sensors: SensorMapping[];
  filters: FilterOptions;
  onFiltersChange: (filters: FilterOptions) => void;
  onReset: () => void;
  isLoading?: boolean;
}

export const DataFilters: React.FC<DataFiltersProps> = ({
  sensors,
  filters,
  onFiltersChange,
  onReset,
  isLoading = false
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const handleFilterChange = (key: keyof FilterOptions, value: string | number | undefined) => {
    onFiltersChange({
      ...filters,
      [key]: value || undefined
    });
  };

  // デフォルト日付範囲（過去7日間）
  const getDefaultDateRange = () => {
    const end = new Date();
    const start = new Date();
    start.setDate(end.getDate() - 7);
    return {
      start: start.toISOString().slice(0, 16), // YYYY-MM-DDTHH:mm形式
      end: end.toISOString().slice(0, 16)
    };
  };

  const defaultDates = getDefaultDateRange();

  return (
    <Card className="mb-6">
      <div className="space-y-4">
        {/* 基本フィルター */}
        <div className="flex flex-wrap gap-4 items-end">
          <div className="flex-1 min-w-48">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              キーワード検索
            </label>
            <Input
              type="text"
              placeholder="センサーIDで検索..."
              value={filters.search || ''}
              onChange={(e) => handleFilterChange('search', e.target.value)}
              disabled={isLoading}
            />
          </div>

          {sensors.length > 1 && (
            <div className="min-w-48">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                センサー選択
              </label>
              <select
                value={filters.sensor_id || ''}
                onChange={(e) => handleFilterChange('sensor_id', e.target.value)}
                disabled={isLoading}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">全てのセンサー</option>
                {sensors.map((sensor) => (
                  <option key={sensor.sensor_id} value={sensor.sensor_id}>
                    {sensor.sensor_id} {sensor.subject_name && `(${sensor.subject_name})`}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div className="flex gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => setIsExpanded(!isExpanded)}
              disabled={isLoading}
            >
              {isExpanded ? '詳細を閉じる' : '詳細フィルター'}
            </Button>
            
            <Button
              type="button"
              variant="outline"
              onClick={onReset}
              disabled={isLoading}
            >
              リセット
            </Button>
          </div>
        </div>

        {/* 詳細フィルター */}
        {isExpanded && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 pt-4 border-t">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                開始日時
              </label>
              <Input
                type="datetime-local"
                value={filters.start_date || defaultDates.start}
                onChange={(e) => handleFilterChange('start_date', e.target.value)}
                disabled={isLoading}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                終了日時
              </label>
              <Input
                type="datetime-local"
                value={filters.end_date || defaultDates.end}
                onChange={(e) => handleFilterChange('end_date', e.target.value)}
                disabled={isLoading}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                最低温度 (°C)
              </label>
              <Input
                type="number"
                step="0.1"
                min="30"
                max="45"
                placeholder="例: 36.0"
                value={filters.min_temperature || ''}
                onChange={(e) => handleFilterChange('min_temperature', e.target.value ? parseFloat(e.target.value) : undefined)}
                disabled={isLoading}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                最高温度 (°C)
              </label>
              <Input
                type="number"
                step="0.1"
                min="30"
                max="45"
                placeholder="例: 38.0"
                value={filters.max_temperature || ''}
                onChange={(e) => handleFilterChange('max_temperature', e.target.value ? parseFloat(e.target.value) : undefined)}
                disabled={isLoading}
              />
            </div>
          </div>
        )}
      </div>
    </Card>
  );
};