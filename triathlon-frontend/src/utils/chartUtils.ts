// src/utils/chartUtils.ts

import { SensorDataPoint, RaceRecord } from '@/types/feedback';

export interface ChartDataPoint {
  timestamp: string;
  temperature?: number;
  sensor_id?: string;
}

export interface FeedbackChartSegment {
  start: number;
  end: number;
  color: string;
  type: 'swim' | 'bike' | 'run';
  label: string;
}

// 既存のformatChartData関数を拡張
export const formatChartData = (data: ChartDataPoint[]) => {
  return {
    labels: data.map(point => new Date(point.timestamp).toLocaleTimeString('ja-JP', { 
      hour: '2-digit', 
      minute: '2-digit' 
    })),
    datasets: [
      {
        label: '体表温度',
        data: data.map(point => point.temperature),
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        borderWidth: 2,
        fill: true,
        tension: 0.4,
        pointBackgroundColor: 'rgb(59, 130, 246)',
        pointBorderColor: 'white',
        pointBorderWidth: 2,
        pointRadius: 3,
        pointHoverRadius: 5,
      }
    ]
  };
};

// フィードバックチャート用のデータフォーマット関数
export const formatFeedbackChartData = (data: SensorDataPoint[]) => {
  if (!data.length) return { labels: [], datasets: [] };

  const labels = data.map(point => 
    new Date(point.timestamp).toLocaleTimeString('ja-JP', {
      hour: '2-digit',
      minute: '2-digit'
    })
  );

  const datasets = [];

  // 体表温度（左軸）
  if (data.some(point => point.skin_temperature !== undefined)) {
    datasets.push({
      label: '体表温度',
      data: data.map(point => point.skin_temperature),
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
  if (data.some(point => point.core_temperature !== undefined)) {
    datasets.push({
      label: 'カプセル体温',
      data: data.map(point => point.core_temperature),
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
  if (data.some(point => point.wbgt_temperature !== undefined)) {
    datasets.push({
      label: 'WBGT温度',
      data: data.map(point => point.wbgt_temperature),
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
  if (data.some(point => point.heart_rate !== undefined)) {
    datasets.push({
      label: '心拍数',
      data: data.map(point => point.heart_rate),
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

// 競技区間の背景色設定を生成
export const generateRaceSegments = (
  raceRecord: RaceRecord | null,
  timeRange: { start: string; end: string } | null
): FeedbackChartSegment[] => {
  if (!raceRecord || !timeRange) return [];

  const segments: FeedbackChartSegment[] = [];
  const canvasStart = new Date(timeRange.start).getTime();
  const canvasEnd = new Date(timeRange.end).getTime();

  // Swim区間 - 薄い水色
  if (raceRecord.swim_start) {
    const swimStart = new Date(raceRecord.swim_start).getTime();
    const swimEnd = raceRecord.swim_finish ? 
      new Date(raceRecord.swim_finish).getTime() : 
      (raceRecord.bike_start ? new Date(raceRecord.bike_start).getTime() : null);
    
    if (swimEnd) {
      segments.push({
        start: Math.max(canvasStart, swimStart),
        end: Math.min(canvasEnd, swimEnd),
        color: 'rgba(191, 219, 254, 0.3)',
        type: 'swim',
        label: 'Swim'
      });
    }
  }

  // Bike区間 - 薄い橙
  if (raceRecord.bike_start) {
    const bikeStart = new Date(raceRecord.bike_start).getTime();
    const bikeEnd = raceRecord.bike_finish ? 
      new Date(raceRecord.bike_finish).getTime() : 
      (raceRecord.run_start ? new Date(raceRecord.run_start).getTime() : null);
    
    if (bikeEnd) {
      segments.push({
        start: Math.max(canvasStart, bikeStart),
        end: Math.min(canvasEnd, bikeEnd),
        color: 'rgba(254, 215, 170, 0.3)',
        type: 'bike',
        label: 'Bike'
      });
    }
  }

  // Run区間 - 薄い黄緑
  if (raceRecord.run_start) {
    const runStart = new Date(raceRecord.run_start).getTime();
    const runEnd = raceRecord.run_finish ? 
      new Date(raceRecord.run_finish).getTime() : canvasEnd;
    
    segments.push({
      start: Math.max(canvasStart, runStart),
      end: Math.min(canvasEnd, runEnd),
      color: 'rgba(187, 247, 208, 0.3)',
      type: 'run',
      label: 'Run'
    });
  }

  return segments;
};

// チャートオプションの生成（フィードバック用）
export const getFeedbackChartOptions = (
  hasTemperatureData: boolean,
  hasHeartRateData: boolean
) => {
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

// 時間範囲の計算
export const calculateTimeRange = (
  raceRecord: RaceRecord | null, 
  offsetMinutes: number
): { start: string; end: string } | null => {
  if (!raceRecord) {
    // 大会記録がない場合のデフォルト範囲
    const now = new Date();
    const oneHourAgo = new Date(now.getTime() - 60 * 60 * 1000);
    return {
      start: oneHourAgo.toISOString(),
      end: now.toISOString()
    };
  }

  // swim開始からrun終了までの範囲を計算
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
  } else if (raceRecord.run_start) {
    // run開始から1時間後と仮定
    endTime = new Date(new Date(raceRecord.run_start).getTime() + 60 * 60 * 1000).toISOString();
  }

  if (startTime && endTime) {
    // オフセットを適用
    const start = new Date(new Date(startTime).getTime() - offsetMinutes * 60 * 1000);
    const end = new Date(new Date(endTime).getTime() + offsetMinutes * 60 * 1000);
    
    return {
      start: start.toISOString(),
      end: end.toISOString()
    };
  }

  return null;
};

// 既存のchartOptions関数（後方互換性のため残す）
export const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'top' as const,
    },
    title: {
      display: true,
      text: 'センサデータ推移',
      font: {
        size: 16,
        weight: 'bold',
      }
    },
    tooltip: {
      callbacks: {
        label: (context: any) => `体表温度: ${context.parsed.y.toFixed(2)}°C`,
        title: (context: any) => {
          const timestamp = context[0]?.label;
          return `時刻: ${timestamp}`;
        }
      }
    }
  },
  scales: {
    x: {
      title: {
        display: true,
        text: '時刻'
      },
      grid: {
        display: true,
        color: 'rgba(0, 0, 0, 0.05)',
      }
    },
    y: {
      title: {
        display: true,
        text: '温度 (°C)'
      },
      grid: {
        display: true,
        color: 'rgba(0, 0, 0, 0.05)',
      },
      suggestedMin: 35.0,
      suggestedMax: 38.0,
    }
  },
  interaction: {
    intersect: false,
    mode: 'index' as const,
  }
};