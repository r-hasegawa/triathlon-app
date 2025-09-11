import React, { useState, useEffect } from 'react';
import { Layout } from '@/components/layout/Layout';
import { Card } from '@/components/ui/Card';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

interface SensorStatus {
  sensor_type: string;
  total_sensors: number;
  mapped_sensors: number;
  unmapped_sensors: number;
  total_records: number;
  latest_upload: string;
}

export const MultiSensorStatus: React.FC = () => {
  const [status, setStatus] = useState<SensorStatus[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    loadStatus();
  }, []);

  const loadStatus = async () => {
    setIsLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:8000/admin/sensors/status', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      const data = await response.json();
      setStatus(data.status || []);
    } catch (error) {
      console.error('Failed to load sensor status:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Layout>
      <div className="space-y-6">
        <h1 className="text-2xl font-bold">センサーステータス</h1>
        
        {isLoading ? (
          <LoadingSpinner />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {status.map((sensor, index) => (
              <Card key={index} className="p-6">
                <h2 className="text-lg font-semibold mb-4">{sensor.sensor_type}</h2>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span>総センサー数:</span>
                    <span className="font-semibold">{sensor.total_sensors}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>マッピング済み:</span>
                    <span className="font-semibold text-green-600">{sensor.mapped_sensors}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>未マッピング:</span>
                    <span className="font-semibold text-yellow-600">{sensor.unmapped_sensors}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>総レコード数:</span>
                    <span className="font-semibold">{sensor.total_records.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>最新アップロード:</span>
                    <span className="text-sm text-gray-600">{sensor.latest_upload}</span>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
};