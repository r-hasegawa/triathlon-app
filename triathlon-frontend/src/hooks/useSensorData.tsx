import { useState, useEffect } from 'react';
import { dataService } from '@/services/dataService';
import { SensorMapping, SensorDataStats } from '@/types/sensor';

export const useSensorData = () => {
  const [sensors, setSensors] = useState<SensorMapping[]>([]);
  const [stats, setStats] = useState<SensorDataStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchData = async () => {
    try {
      setIsLoading(true);
      setError('');
      
      const [sensorsData, statsData] = await Promise.all([
        dataService.getMySensors(),
        dataService.getMyDataStats()
      ]);
      
      setSensors(sensorsData);
      setStats(statsData);
    } catch (err: any) {
      console.error('Error fetching sensor data:', err);
      setError('データの取得に失敗しました');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const refetch = () => {
    fetchData();
  };

  return {
    sensors,
    stats,
    isLoading,
    error,
    refetch,
  };
};