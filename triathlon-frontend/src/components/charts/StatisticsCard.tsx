import React from 'react';
import { SensorDataStats } from '@/types/sensor';
import { Card } from '@/components/ui/Card';

interface StatisticsCardProps {
  stats: SensorDataStats;
  isLoading?: boolean;
}

export const StatisticsCard: React.FC<StatisticsCardProps> = ({ 
  stats, 
  isLoading = false 
}) => {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[...Array(4)].map((_, i) => (
          <Card key={i}>
            <div className="animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-1/2 mb-2"></div>
              <div className="h-8 bg-gray-200 rounded w-3/4 mb-1"></div>
              <div className="h-3 bg-gray-200 rounded w-1/3"></div>
            </div>
          </Card>
        ))}
      </div>
    );
  }

  const formatTemperature = (temp: number | null) => {
    return temp ? `${temp.toFixed(1)}°C` : 'データなし';
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'データなし';
    return new Date(dateString).toLocaleDateString('ja-JP', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <Card>
        <div className="text-center">
          <p className="text-sm font-medium text-gray-500 mb-1">総データ数</p>
          <p className="text-2xl font-bold text-blue-600 mb-1">
            {stats.total_records.toLocaleString()}
          </p>
          <p className="text-xs text-gray-400">件のデータ</p>
        </div>
      </Card>
      
      <Card>
        <div className="text-center">
          <p className="text-sm font-medium text-gray-500 mb-1">平均体温</p>
          <p className="text-2xl font-bold text-green-600 mb-1">
            {formatTemperature(stats.avg_temperature)}
          </p>
          <p className="text-xs text-gray-400">Average</p>
        </div>
      </Card>
      
      <Card>
        <div className="text-center">
          <p className="text-sm font-medium text-gray-500 mb-1">最高体温</p>
          <p className="text-2xl font-bold text-red-600 mb-1">
            {formatTemperature(stats.max_temperature)}
          </p>
          <p className="text-xs text-gray-400">Maximum</p>
        </div>
      </Card>
      
      <Card>
        <div className="text-center">
          <p className="text-sm font-medium text-gray-500 mb-1">最低体温</p>
          <p className="text-2xl font-bold text-blue-600 mb-1">
            {formatTemperature(stats.min_temperature)}
          </p>
          <p className="text-xs text-gray-400">Minimum</p>
        </div>
      </Card>
    </div>
  );
};