// TriathlonFeedbackChart.tsx - 時間範囲選択対応版

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
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { feedbackService } from '@/services/feedbackService';
import type { CompetitionRace, SensorDataPoint, RaceRecord } from '@/services/feedbackService';

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

interface TriathlonFeedbackChartProps {
  userId?: string;
  competitionId?: string;
  competitions?: CompetitionRace[];
  height?: number;
  className?: string;
  isAdminView?: boolean;
}

interface TimeRange {
  start: string;
  end: string;
}

export const TriathlonFeedbackChart: React.FC<TriathlonFeedbackChartProps> = ({
  userId,
  competitionId,
  competitions = [],
  height = 500,
  className = '',
  isAdminView = false,
}) => {
  const [selectedCompetition, setSelectedCompetition] = useState<string>(
    competitionId || ''
  );
  const [sensorData, setSensorData] = useState<SensorDataPoint[]>([]);
  const [raceRecord, setRaceRecord] = useState<RaceRecord | null>(null);
  const [timeRange, setTimeRange] = useState<TimeRange | null>(null);
  const [customTimeRange, setCustomTimeRange] = useState<TimeRange | null>(null);
  const [timeRangeMode, setTimeRangeMode] = useState<'auto' | 'race' | 'custom'>('auto');
  const [offsetMinutes, setOffsetMinutes] = useState<number>(10);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  // デフォルトで最新の大会を選択
  useEffect(() => {
    if (!selectedCompetition && competitions.length > 0) {
      const latestCompetition = competitions.reduce((latest, comp) => 
        new Date(comp.date) > new Date(latest.date) ? comp : latest
      );
      setSelectedCompetition(latestCompetition.id);
    }
  }, [competitions, selectedCompetition]);

  // 選択された大会が変更されたらデータを取得
  useEffect(() => {
    if (selectedCompetition) {
      fetchFeedbackData();
    }
  }, [selectedCompetition]);

  // 時間範囲モードまたはオフセットが変更されたら再計算
  useEffect(() => {
    if (sensorData.length > 0) {
      calculateTimeRange();
    }
  }, [timeRangeMode, offsetMinutes, raceRecord, sensorData]);

  const fetchFeedbackData = async () => {
    try {
      setIsLoading(true);
      setError('');

      if (!selectedCompetition) {
        setError('大会が選択されていません');
        return;
      }

      console.log('Fetching feedback data for competition:', selectedCompetition);

      let feedbackData;
      
      try {
        if (isAdminView && userId) {
          console.log('Using admin API for user:', userId);
          feedbackData = await feedbackService.getAdminUserFeedbackData(userId, selectedCompetition);
        } else {
          console.log('Using regular user API');
          feedbackData = await feedbackService.getFeedbackData(selectedCompetition);
        }
        
        console.log('Feedback data received:', {
          sensorDataCount: feedbackData.sensor_data?.length || 0,
          raceRecord: feedbackData.race_record,
          competition: feedbackData.competition
        });

        setSensorData(feedbackData.sensor_data || []);
        setRaceRecord(feedbackData.race_record);

      } catch (apiError: any) {
        console.error('API failed:', apiError);
        setError(`データ取得エラー: ${apiError.message}`);
        setSensorData([]);
        setRaceRecord(null);
      }

    } catch (err: any) {
      console.error('Feedback data fetch error:', err);
      setError(err.message || 'データの取得に失敗しました');
      setSensorData([]);
      setRaceRecord(null);
    } finally {
      setIsLoading(false);
    }
  };

  const calculateTimeRange = () => {
    if (timeRangeMode === 'custom' && customTimeRange) {
      setTimeRange(customTimeRange);
      return;
    }

    if (timeRangeMode === 'race' && raceRecord) {
      // 大会記録ベースの時間範囲
      let startTime: string | null = null;
      let endTime: string | null = null;

      if (raceRecord.swim_start) {
        startTime = raceRecord.swim_start;
      } else if (raceRecord.bike_start) {
        startTime = raceRecord.bike_start;
      } else if (raceRecord.run_start) {
        startTime = raceRecord.run_start;
      }

      if (raceRecord.run_finish) {
        endTime = raceRecord.run_finish;
      } else if (raceRecord.bike_finish) {
        endTime = raceRecord.bike_finish;
      } else if (raceRecord.swim_finish) {
        endTime = raceRecord.swim_finish;
      }

      if (startTime && endTime) {
        const start = new Date(new Date(startTime).getTime() - offsetMinutes * 60 * 1000);
        const end = new Date(new Date(endTime).getTime() + offsetMinutes * 60 * 1000);
        
        setTimeRange({
          start: start.toISOString(),
          end: end.toISOString()
        });
        
        console.log('Race-based time range:', {
          start: start.toISOString(),
          end: end.toISOString(),
          offset: offsetMinutes
        });
        return;
      }
    }

    // auto: センサーデータベースの時間範囲
    if (sensorData.length > 0) {
      const timestamps = sensorData
        .map(d => new Date(d.timestamp))
        .sort((a, b) => a.getTime() - b.getTime());
      
      const startTime = timestamps[0];
      const endTime = timestamps[timestamps.length - 1];
      
      const start = new Date(startTime.getTime() - offsetMinutes * 60 * 1000);
      const end = new Date(endTime.getTime() + offsetMinutes * 60 * 1000);
      
      setTimeRange({
        start: start.toISOString(),
        end: end.toISOString()
      });
      
      console.log('Auto time range from sensor data:', {
        start: start.toISOString(),
        end: end.toISOString(),
        dataPoints: sensorData.length,
        offset: offsetMinutes
      });
    }
  };

  const formatChartData = () => {
    if (!sensorData.length) return { labels: [], datasets: [] };

    // 時間範囲でフィルタリング
    let filteredData = sensorData;
    if (timeRange) {
      const startTime = new Date(timeRange.start);
      const endTime = new Date(timeRange.end);
      
      filteredData = sensorData.filter(data => {
        const dataTime = new Date(data.timestamp);
        return dataTime >= startTime && dataTime <= endTime;
      });
      
      console.log(`Filtered data: ${filteredData.length} / ${sensorData.length} points`);
    }

    if (filteredData.length === 0) {
      console.warn('No data points after filtering');
      return { labels: [], datasets: [] };
    }

    const labels = filteredData.map(point => 
      new Date(point.timestamp).toLocaleTimeString('ja-JP', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      })
    );

    const datasets = [];

    // 体表温度（左軸）
    if (filteredData.some(point => point.skin_temperature !== undefined && point.skin_temperature !== null)) {
      datasets.push({
        label: '体表温度',
        data: filteredData.map(point => point.skin_temperature),
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        borderWidth: 2,
        tension: 0.4,
        yAxisID: 'y',
        pointRadius: 0.5,
        pointHoverRadius: 5,
      });
    }

    // カプセル体温度（左軸）
    if (filteredData.some(point => point.core_temperature !== undefined && point.core_temperature !== null)) {
      datasets.push({
        label: 'カプセル体温',
        data: filteredData.map(point => point.core_temperature),
        borderColor: 'rgb(239, 68, 68)',
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
        borderWidth: 2,
        tension: 0.4,
        yAxisID: 'y',
        pointRadius: 0.5,
        pointHoverRadius: 5,
      });
    }

    // WBGT温度（左軸）
    if (filteredData.some(point => point.wbgt_temperature !== undefined && point.wbgt_temperature !== null)) {
      datasets.push({
        label: 'WBGT温度',
        data: filteredData.map(point => point.wbgt_temperature),
        borderColor: 'rgb(245, 158, 11)',
        backgroundColor: 'rgba(245, 158, 11, 0.1)',
        borderWidth: 2,
        tension: 0.4,
        yAxisID: 'y',
        pointRadius: 0.5,
        pointHoverRadius: 5,
      });
    }

    // 心拍数（右軸）
    if (filteredData.some(point => point.heart_rate !== undefined && point.heart_rate !== null)) {
      datasets.push({
        label: '心拍数',
        data: filteredData.map(point => point.heart_rate),
        borderColor: 'rgb(34, 197, 94)',
        backgroundColor: 'rgba(34, 197, 94, 0.1)',
        borderWidth: 2,
        tension: 0.4,
        yAxisID: 'y1',
        pointRadius: 0.5,
        pointHoverRadius: 5,
      });
    }

    return { labels, datasets };
  };

  const getChartOptions = () => {
    const hasTemperatureData = sensorData.some(point => 
      point.skin_temperature !== undefined || 
      point.core_temperature !== undefined || 
      point.wbgt_temperature !== undefined
    );
    
    const hasHeartRateData = sensorData.some(point => point.heart_rate !== undefined);

    return {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top' as const,
        },
        title: {
          display: true,
          text: 'トライアスロン フィードバックグラフ',
          font: {
            size: 16,
            weight: 'bold',
          }
        },
        tooltip: {
          callbacks: {
            label: (context: any) => {
              const label = context.dataset.label;
              const value = context.parsed.y;
              if (label === '心拍数') {
                return `${label}: ${value?.toFixed(0)} bpm`;
              } else {
                return `${label}: ${value?.toFixed(1)}°C`;
              }
            }
          }
        }
      },
      scales: {
        x: {
          title: {
            display: true,
            text: '時間'
          },
          grid: {
            display: true,
            color: 'rgba(0, 0, 0, 0.05)',
          }
        },
        ...(hasTemperatureData && {
          y: {
            type: 'linear' as const,
            display: true,
            position: 'left' as const,
            title: {
              display: true,
              text: '温度 (°C)'
            },
            grid: {
              display: true,
              color: 'rgba(0, 0, 0, 0.05)',
            },
            suggestedMin: 25,
            suggestedMax: 40,
          }
        }),
        ...(hasHeartRateData && {
          y1: {
            type: 'linear' as const,
            display: true,
            position: 'right' as const,
            title: {
              display: true,
              text: '心拍数 (bpm)'
            },
            grid: {
              drawOnChartArea: false,
            },
            suggestedMin: 60,
            suggestedMax: 200,
          }
        })
      },
      interaction: {
        intersect: false,
        mode: 'index' as const,
      }
    };
  };

  const handleRefresh = () => {
    fetchFeedbackData();
  };

  const handleCustomTimeRangeChange = (field: 'start' | 'end', value: string) => {
    const newCustomRange = {
      ...customTimeRange,
      [field]: value
    } as TimeRange;
    setCustomTimeRange(newCustomRange);
    
    if (timeRangeMode === 'custom') {
      setTimeRange(newCustomRange);
    }
  };

  // センサーデータの時間範囲を取得
  const getDataTimeRange = () => {
    if (sensorData.length === 0) return null;
    
    const timestamps = sensorData.map(d => new Date(d.timestamp));
    const minTime = new Date(Math.min(...timestamps.map(t => t.getTime())));
    const maxTime = new Date(Math.max(...timestamps.map(t => t.getTime())));
    
    return {
      start: minTime.toISOString().slice(0, 16),
      end: maxTime.toISOString().slice(0, 16)
    };
  };

  const dataTimeRange = getDataTimeRange();

  return (
    <Card className={`p-6 ${className}`}>
      <div className="space-y-4">
        {/* コントロール */}
        <div className="flex flex-wrap gap-4 items-center justify-between">
          <div className="flex flex-wrap gap-4 items-center">
            {/* 大会選択 */}
            {competitions.length > 1 && (
              <div className="flex items-center gap-2">
                <label className="text-sm font-medium text-gray-700">大会:</label>
                <select
                  value={selectedCompetition}
                  onChange={(e) => setSelectedCompetition(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">大会を選択してください</option>
                  {competitions.map((comp) => (
                    <option key={comp.id} value={comp.id}>
                      {comp.name} ({new Date(comp.date).toLocaleDateString('ja-JP')})
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* 時間範囲モード選択 */}
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium text-gray-700">時間範囲:</label>
              <select
                value={timeRangeMode}
                onChange={(e) => setTimeRangeMode(e.target.value as 'auto' | 'race' | 'custom')}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="auto">自動（センサーデータ範囲）</option>
                <option value="race">大会記録範囲</option>
                <option value="custom">カスタム</option>
              </select>
            </div>

            {/* オフセット設定 */}
            {(timeRangeMode === 'auto' || timeRangeMode === 'race') && (
              <div className="flex items-center gap-2">
                <label className="text-sm font-medium text-gray-700">前後:</label>
                <select
                  value={offsetMinutes}
                  onChange={(e) => setOffsetMinutes(Number(e.target.value))}
                  className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value={0}>0分</option>
                  <option value={5}>5分</option>
                  <option value={10}>10分</option>
                  <option value={15}>15分</option>
                  <option value={30}>30分</option>
                  <option value={60}>60分</option>
                </select>
              </div>
            )}
          </div>

          <Button
            onClick={handleRefresh}
            disabled={isLoading || !selectedCompetition}
            variant="outline"
            size="sm"
          >
            {isLoading ? '更新中...' : '更新'}
          </Button>
        </div>

        {/* カスタム時間範囲設定 */}
        {timeRangeMode === 'custom' && (
          <div className="bg-gray-50 p-4 rounded-lg">
            <h3 className="text-sm font-medium text-gray-700 mb-2">カスタム時間範囲</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-gray-600 mb-1">開始時刻:</label>
                <input
                  type="datetime-local"
                  value={customTimeRange?.start?.slice(0, 16) || dataTimeRange?.start || ''}
                  onChange={(e) => handleCustomTimeRangeChange('start', e.target.value + ':00')}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">終了時刻:</label>
                <input
                  type="datetime-local"
                  value={customTimeRange?.end?.slice(0, 16) || dataTimeRange?.end || ''}
                  onChange={(e) => handleCustomTimeRangeChange('end', e.target.value + ':00')}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
            {dataTimeRange && (
              <p className="text-xs text-gray-500 mt-2">
                データ範囲: {new Date(dataTimeRange.start).toLocaleString('ja-JP')} 〜 {new Date(dataTimeRange.end).toLocaleString('ja-JP')}
              </p>
            )}
          </div>
        )}

        {/* エラー表示 */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-3">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        {/* 大会情報 */}
        {selectedCompetition && competitions.find(c => c.id === selectedCompetition) && (
          <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-blue-700">選択中の大会:</span>
              <span className="text-sm text-blue-600">
                {competitions.find(c => c.id === selectedCompetition)?.name}
              </span>
              <span className="text-xs text-blue-500">
                ({new Date(competitions.find(c => c.id === selectedCompetition)?.date || '').toLocaleDateString('ja-JP')})
              </span>
            </div>
          </div>
        )}

        {/* グラフ */}
        <div className="relative border rounded-lg p-4" style={{ height: `${height}px` }}>
          {isLoading ? (
            <div className="absolute inset-0 flex justify-center items-center">
              <LoadingSpinner size="lg" text="データを読み込んでいます..." />
            </div>
          ) : !selectedCompetition ? (
            <div className="absolute inset-0 flex justify-center items-center">
              <div className="text-center text-gray-500">
                <p className="text-lg font-medium">大会を選択してください</p>
                <p className="text-sm mt-1">
                  大会を選択すると、その大会でのセンサーデータと競技区間が表示されます
                </p>
              </div>
            </div>
          ) : sensorData.length === 0 ? (
            <div className="absolute inset-0 flex justify-center items-center">
              <div className="text-center text-gray-500">
                <p className="text-lg font-medium">表示するデータがありません</p>
                <p className="text-sm mt-1">
                  選択された大会にセンサーデータが登録されていません
                </p>
              </div>
            </div>
          ) : (
            <div className="h-full">
              <Line data={formatChartData()} options={getChartOptions()} />
            </div>
          )}
        </div>

        {/* データ情報 */}
        {sensorData.length > 0 && selectedCompetition && (
          <div className="flex justify-between text-sm text-gray-500">
            <span>
              {formatChartData().labels.length}/{sensorData.length}件のデータポイントを表示中
            </span>
            {timeRange && (
              <span>
                表示範囲: {new Date(timeRange.start).toLocaleTimeString('ja-JP')} - {' '}
                {new Date(timeRange.end).toLocaleTimeString('ja-JP')}
              </span>
            )}
          </div>
        )}

        {/* 競技区間の凡例 */}
        {raceRecord && timeRangeMode === 'race' && (
          <div className="flex flex-wrap gap-4 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded" style={{ backgroundColor: 'rgba(191, 219, 254, 0.6)' }}></div>
              <span>Swim ({raceRecord.swim_start ? new Date(raceRecord.swim_start).toLocaleTimeString('ja-JP') : '未設定'})</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded" style={{ backgroundColor: 'rgba(254, 215, 170, 0.6)' }}></div>
              <span>Bike ({raceRecord.bike_start ? new Date(raceRecord.bike_start).toLocaleTimeString('ja-JP') : '未設定'})</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded" style={{ backgroundColor: 'rgba(187, 247, 208, 0.6)' }}></div>
              <span>Run ({raceRecord.run_start ? new Date(raceRecord.run_start).toLocaleTimeString('ja-JP') : '未設定'})</span>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
};