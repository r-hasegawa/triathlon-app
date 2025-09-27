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

// 型定義を削除（feedbackServiceからインポートするため）
interface TriathlonFeedbackChartProps {
  userId?: string;
  competitionId?: string;
  competitions?: CompetitionRace[];
  height?: number;
  className?: string;
}

export const TriathlonFeedbackChart: React.FC<TriathlonFeedbackChartProps> = ({
  userId,
  competitionId,
  competitions = [],
  height = 500,
  className = '',
}) => {
  const [selectedCompetition, setSelectedCompetition] = useState<string>(
    competitionId || ''
  );
  const [sensorData, setSensorData] = useState<SensorDataPoint[]>([]);
  const [raceRecord, setRaceRecord] = useState<RaceRecord | null>(null);
  const [timeRange, setTimeRange] = useState<{
    start: string;
    end: string;
  } | null>(null);
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
    if (selectedCompetition && userId) {
      fetchFeedbackData();
    }
  }, [selectedCompetition, userId]);

  const fetchFeedbackData = async () => {
    try {
      setIsLoading(true);
      setError('');

      if (!selectedCompetition) {
        setError('大会が選択されていません');
        return;
      }

      console.log('Fetching feedback data for competition:', selectedCompetition);

      // センサーデータと大会記録を個別に取得（エラーハンドリング改善）
      let sensorData: SensorDataPoint[] = [];
      let raceRecord: RaceRecord | null = null;

      try {
        sensorData = await feedbackService.getSensorData(selectedCompetition);
        console.log('Sensor data received:', sensorData.length, 'records');
      } catch (sensorError) {
        console.warn('Sensor data fetch failed:', sensorError);
        // センサーデータの取得に失敗してもエラーとしない
      }

      try {
        raceRecord = await feedbackService.getRaceRecord(selectedCompetition);
        console.log('Race record received:', raceRecord);
      } catch (raceError) {
        console.warn('Race record fetch failed:', raceError);
        // 大会記録の取得に失敗してもエラーとしない
      }

      setSensorData(sensorData || []);
      setRaceRecord(raceRecord);

      // 時間範囲の設定
      calculateTimeRange(raceRecord);

    } catch (err: any) {
      console.error('Feedback data fetch error:', err);
      setError(err.message || 'データの取得に失敗しました');
    } finally {
      setIsLoading(false);
    }
  };

  const calculateTimeRange = (race: RaceRecord | null) => {
    if (!race) {
      // 大会記録がない場合のデフォルト範囲
      const now = new Date();
      const oneHourAgo = new Date(now.getTime() - 60 * 60 * 1000);
      setTimeRange({
        start: oneHourAgo.toISOString(),
        end: now.toISOString()
      });
      return;
    }

    // swim開始からrun終了までの範囲を計算
    const startTime = race.swim_start;
    let endTime = race.run_finish;

    // 仕様に従って欠損データを補完
    if (!race.swim_finish && race.bike_start) {
      race.swim_finish = race.bike_start;
    }
    if (!race.bike_finish && race.run_start) {
      race.bike_finish = race.run_start;
    }

    if (startTime && endTime) {
      // オフセットを適用
      const start = new Date(new Date(startTime).getTime() - offsetMinutes * 60 * 1000);
      const end = new Date(new Date(endTime).getTime() + offsetMinutes * 60 * 1000);
      
      setTimeRange({
        start: start.toISOString(),
        end: end.toISOString()
      });
    }
  };

  const formatChartData = () => {
    if (!sensorData.length) return { labels: [], datasets: [] };

    // 時間範囲でフィルタリング
    const filteredData = timeRange 
      ? sensorData.filter(point => {
          const timestamp = new Date(point.timestamp);
          return timestamp >= new Date(timeRange.start) && timestamp <= new Date(timeRange.end);
        })
      : sensorData;

    const labels = filteredData.map(point => 
      new Date(point.timestamp).toLocaleTimeString('ja-JP', {
        hour: '2-digit',
        minute: '2-digit'
      })
    );

    const datasets = [];

    // 体表温度（左軸）
    if (filteredData.some(point => point.skin_temperature !== undefined)) {
      datasets.push({
        label: '体表温度',
        data: filteredData.map(point => point.skin_temperature),
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        borderWidth: 2,
        tension: 0.4,
        yAxisID: 'y',
        pointRadius: 1,
        pointHoverRadius: 5,
      });
    }

    // カプセル体温度（左軸）
    if (filteredData.some(point => point.core_temperature !== undefined)) {
      datasets.push({
        label: 'カプセル体温',
        data: filteredData.map(point => point.core_temperature),
        borderColor: 'rgb(239, 68, 68)',
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
        borderWidth: 2,
        tension: 0.4,
        yAxisID: 'y',
        pointRadius: 1,
        pointHoverRadius: 5,
      });
    }

    // WBGT温度（左軸）
    if (filteredData.some(point => point.wbgt_temperature !== undefined)) {
      datasets.push({
        label: 'WBGT温度',
        data: filteredData.map(point => point.wbgt_temperature),
        borderColor: 'rgb(245, 158, 11)',
        backgroundColor: 'rgba(245, 158, 11, 0.1)',
        borderWidth: 2,
        tension: 0.4,
        yAxisID: 'y',
        pointRadius: 1,
        pointHoverRadius: 5,
      });
    }

    // 心拍数（右軸）
    if (filteredData.some(point => point.heart_rate !== undefined)) {
      datasets.push({
        label: '心拍数',
        data: filteredData.map(point => point.heart_rate),
        borderColor: 'rgb(34, 197, 94)',
        backgroundColor: 'rgba(34, 197, 94, 0.1)',
        borderWidth: 2,
        tension: 0.4,
        yAxisID: 'y1',
        pointRadius: 1,
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

  // 背景色の設定（競技区間）
  const getBackgroundSegments = () => {
    if (!raceRecord || !timeRange) return [];

    const segments = [];
    const canvasStart = new Date(timeRange.start);
    const canvasEnd = new Date(timeRange.end);

    // Swim区間 - 薄い水色
    if (raceRecord.swim_start) {
      const swimStart = new Date(raceRecord.swim_start);
      const swimEnd = raceRecord.swim_finish ? new Date(raceRecord.swim_finish) : 
                     (raceRecord.bike_start ? new Date(raceRecord.bike_start) : null);
      
      if (swimEnd) {
        segments.push({
          start: Math.max(canvasStart.getTime(), swimStart.getTime()),
          end: Math.min(canvasEnd.getTime(), swimEnd.getTime()),
          color: 'rgba(191, 219, 254, 0.3)' // 薄い水色
        });
      }
    }

    // Bike区間 - 薄い橙
    if (raceRecord.bike_start) {
      const bikeStart = new Date(raceRecord.bike_start);
      const bikeEnd = raceRecord.bike_finish ? new Date(raceRecord.bike_finish) : 
                     (raceRecord.run_start ? new Date(raceRecord.run_start) : null);
      
      if (bikeEnd) {
        segments.push({
          start: Math.max(canvasStart.getTime(), bikeStart.getTime()),
          end: Math.min(canvasEnd.getTime(), bikeEnd.getTime()),
          color: 'rgba(254, 215, 170, 0.3)' // 薄い橙
        });
      }
    }

    // Run区間 - 薄い黄緑
    if (raceRecord.run_start) {
      const runStart = new Date(raceRecord.run_start);
      const runEnd = raceRecord.run_finish ? new Date(raceRecord.run_finish) : canvasEnd;
      
      segments.push({
        start: Math.max(canvasStart.getTime(), runStart.getTime()),
        end: Math.min(canvasEnd.getTime(), runEnd.getTime()),
        color: 'rgba(187, 247, 208, 0.3)' // 薄い黄緑
      });
    }

    return segments;
  };

  const handleRefresh = () => {
    fetchFeedbackData();
  };

  const handleOffsetChange = (newOffset: number) => {
    setOffsetMinutes(newOffset);
    if (raceRecord) {
      calculateTimeRange(raceRecord);
    }
  };

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

            {/* オフセット設定 */}
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium text-gray-700">前後:</label>
              <select
                value={offsetMinutes}
                onChange={(e) => handleOffsetChange(Number(e.target.value))}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value={0}>0分</option>
                <option value={5}>5分</option>
                <option value={10}>10分</option>
                <option value={15}>15分</option>
                <option value={30}>30分</option>
              </select>
            </div>
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
            <>
              {/* 背景色（競技区間） */}
              <div className="absolute inset-4 flex">
                {getBackgroundSegments().map((segment, index) => {
                  const totalDuration = timeRange ? 
                    new Date(timeRange.end).getTime() - new Date(timeRange.start).getTime() : 1;
                  const segmentStart = timeRange ?
                    (segment.start - new Date(timeRange.start).getTime()) / totalDuration * 100 : 0;
                  const segmentWidth = 
                    (segment.end - segment.start) / totalDuration * 100;

                  return (
                    <div
                      key={index}
                      className="absolute h-full"
                      style={{
                        left: `${segmentStart}%`,
                        width: `${segmentWidth}%`,
                        backgroundColor: segment.color,
                        borderRadius: '4px',
                      }}
                    />
                  );
                })}
              </div>
              
              {/* チャート */}
              <div className="relative z-10 h-full">
                <Line data={formatChartData()} options={getChartOptions()} />
              </div>
            </>
          )}
        </div>

        {/* データ情報 */}
        {sensorData.length > 0 && selectedCompetition && (
          <div className="flex justify-between text-sm text-gray-500">
            <span>
              {sensorData.length}件のデータポイントを表示中
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
        {raceRecord && (
          <div className="flex flex-wrap gap-4 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded" style={{ backgroundColor: 'rgba(191, 219, 254, 0.6)' }}></div>
              <span>Swim</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded" style={{ backgroundColor: 'rgba(254, 215, 170, 0.6)' }}></div>
              <span>Bike</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded" style={{ backgroundColor: 'rgba(187, 247, 208, 0.6)' }}></div>
              <span>Run</span>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
};