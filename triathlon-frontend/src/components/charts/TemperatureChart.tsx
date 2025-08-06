import React, { useState, useEffect } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import { dataService } from '@/services/dataService';
import { ChartDataPoint, SensorMapping } from '@/types/sensor';
import { formatChartData, chartOptions } from '@/utils/chartUtils';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

// Chart.jsのコンポーネントを登録
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface TemperatureChartProps {
  sensors?: SensorMapping[];
  height?: number;
}

export const TemperatureChart: React.FC<TemperatureChartProps> = ({ 
  sensors = [], 
  height = 400 
}) => {
  const [chartData, setChartData] = useState<ChartDataPoint[]>([]);
  const [selectedSensorId, setSelectedSensorId] = useState<string>('');
  const [timeRange, setTimeRange] = useState<'1hour' | '6hour' | '24hour' | '7day'>('24hour');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchChartData();
  }, [selectedSensorId, timeRange]);

  const fetchChartData = async () => {
    try {
      setIsLoading(true);
      setError('');

      // 時間範囲の計算
      const endDate = new Date();
      const startDate = new Date();
      
      switch (timeRange) {
        case '1hour':
          startDate.setHours(endDate.getHours() - 1);
          break;
        case '6hour':
          startDate.setHours(endDate.getHours() - 6);
          break;
        case '24hour':
          startDate.setDate(endDate.getDate() - 1);
          break;
        case '7day':
          startDate.setDate(endDate.getDate() - 7);
          break;
      }

      // データ間隔の決定
      let interval: '1min' | '5min' | '15min' | '1hour' | '1day';
      switch (timeRange) {
        case '1hour':
          interval = '1min';
          break;
        case '6hour':
          interval = '5min';
          break;
        case '24hour':
          interval = '15min';
          break;
        case '7day':
          interval = '1hour';
          break;
      }

      const response = await dataService.getChartData({
        sensor_id: selectedSensorId || undefined,
        start_date: startDate.toISOString(),
        end_date: endDate.toISOString(),
        interval,
      });

      setChartData(response.data);
    } catch (err: any) {
      console.error('Chart data fetch error:', err);
      setError('グラフデータの取得に失敗しました');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRefresh = () => {
    fetchChartData();
  };

  return (
    <Card>
      <div className="space-y-4">
        {/* コントロール */}
        <div className="flex flex-wrap gap-4 items-center justify-between">
          <div className="flex flex-wrap gap-2">
            {/* センサー選択 */}
            {sensors.length > 1 && (
              <select
                value={selectedSensorId}
                onChange={(e) => setSelectedSensorId(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">全てのセンサー</option>
                {sensors.map((sensor) => (
                  <option key={sensor.sensor_id} value={sensor.sensor_id}>
                    {sensor.sensor_id} {sensor.subject_name && `(${sensor.subject_name})`}
                  </option>
                ))}
              </select>
            )}

            {/* 時間範囲選択 */}
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value as any)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="1hour">直近1時間</option>
              <option value="6hour">直近6時間</option>
              <option value="24hour">直近24時間</option>
              <option value="7day">直近7日間</option>
            </select>
          </div>

          <Button
            onClick={handleRefresh}
            disabled={isLoading}
            variant="outline"
            size="sm"
          >
            {isLoading ? '更新中...' : '更新'}
          </Button>
        </div>

        {/* エラー表示 */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-3">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        {/* グラフ */}
        <div className="relative" style={{ height: `${height}px` }}>
          {isLoading ? (
            <div className="absolute inset-0 flex justify-center items-center">
              <LoadingSpinner size="lg" />
            </div>
          ) : chartData.length === 0 ? (
            <div className="absolute inset-0 flex justify-center items-center">
              <div className="text-center text-gray-500">
                <p>表示するデータがありません</p>
                <p className="text-sm mt-1">時間範囲またはセンサーを変更してみてください</p>
              </div>
            </div>
          ) : (
            <Line data={formatChartData(chartData)} options={chartOptions} />
          )}
        </div>

        {/* データ情報 */}
        {chartData.length > 0 && (
          <div className="text-sm text-gray-500 text-center">
            {chartData.length}件のデータポイントを表示中
            {selectedSensorId && ` (センサー: ${selectedSensorId})`}
          </div>
        )}
      </div>
    </Card>
  );
};