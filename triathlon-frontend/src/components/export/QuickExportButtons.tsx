import React from 'react';
import { Button } from '@/components/ui/Button';
import { dataService } from '@/services/dataService';
import { FilterOptions } from '@/components/data/DataFilters';

interface QuickExportButtonsProps {
  filters: FilterOptions;
  disabled?: boolean;
  className?: string;
}

export const QuickExportButtons: React.FC<QuickExportButtonsProps> = ({
  filters,
  disabled = false,
  className = ''
}) => {
  const handleQuickExport = async (format: 'csv' | 'json') => {
    try {
      const blob = await dataService.exportData(format, filters);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      
      const timestamp = new Date().toISOString().slice(0, 10);
      const sensorId = filters.sensor_id ? `_${filters.sensor_id}` : '';
      link.download = `sensor_data${sensorId}_${timestamp}.${format}`;
      
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error: any) {
      console.error('Quick export error:', error);
      alert(`エクスポートに失敗しました: ${error.message}`);
    }
  };

  return (
    <div className={`flex space-x-2 ${className}`}>
      <Button
        variant="outline"
        size="sm"
        onClick={() => handleQuickExport('csv')}
        disabled={disabled}
      >
        📊 CSV
      </Button>
      
      <Button
        variant="outline"  
        size="sm"
        onClick={() => handleQuickExport('json')}
        disabled={disabled}
      >
        📋 JSON
      </Button>
    </div>
  );
};