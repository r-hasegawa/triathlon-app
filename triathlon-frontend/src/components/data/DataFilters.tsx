import React from 'react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { SensorMapping } from '@/types/sensor';

export interface FilterOptions {
  sensor_id?: string;
  sensor_type?: string;
  start_date?: string;
  end_date?: string;
  competition_id?: string;
}

interface DataFiltersProps {
  sensors: SensorMapping[];
  filters: FilterOptions;
  onFiltersChange: (filters: FilterOptions) => void;
  onReset: () => void;
}

export const DataFilters: React.FC<DataFiltersProps> = ({
  sensors,
  filters,
  onFiltersChange,
  onReset,
}) => {
  const handleFilterChange = (key: keyof FilterOptions, value: string) => {
    onFiltersChange({
      ...filters,
      [key]: value || undefined,
    });
  };

  const uniqueSensorTypes = [...new Set(sensors.map(s => s.sensor_type))];

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">フィルター</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div>
          <label className="block text-sm font-medium mb-1">センサーID</label>
          <Input
            placeholder="センサーIDで検索"
            value={filters.sensor_id || ''}
            onChange={(e) => handleFilterChange('sensor_id', e.target.value)}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">センサータイプ</label>
          <select
            value={filters.sensor_type || ''}
            onChange={(e) => handleFilterChange('sensor_type', e.target.value)}
            className="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">すべて</option>
            {uniqueSensorTypes.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">開始日時</label>
          <Input
            type="datetime-local"
            value={filters.start_date || ''}
            onChange={(e) => handleFilterChange('start_date', e.target.value)}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">終了日時</label>
          <Input
            type="datetime-local"
            value={filters.end_date || ''}
            onChange={(e) => handleFilterChange('end_date', e.target.value)}
          />
        </div>
      </div>

      <div className="flex space-x-2">
        <Button
          variant="outline"
          onClick={onReset}
        >
          フィルターをリセット
        </Button>
        
        <div className="flex items-center text-sm text-gray-600">
          {Object.values(filters).filter(Boolean).length > 0 && (
            <span>
              {Object.values(filters).filter(Boolean).length} 個のフィルターが適用中
            </span>
          )}
        </div>
      </div>
    </div>
  );
};