// TriathlonFeedbackChart.tsx - 管理者コメント機能追加版

import React, { useState, useEffect, useMemo, useCallback } from 'react';
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
  TimeScale, // ← 追加
} from 'chart.js';
import 'chartjs-adapter-date-fns'; // ← 追加（npm install chartjs-adapter-date-fns が必要）
import { Line } from 'react-chartjs-2';
import { feedbackService } from '@/services/feedbackService';
import type { CompetitionRace, SensorDataPoint, RaceRecord } from '@/services/feedbackService';

// 🆕 背景色プラグインの定義（正しいアプローチ）
const segmentBackgroundPlugin = {
  id: 'segmentBackground',
  beforeDraw: (chart: any, args: any, options: any) => {
    const { ctx, chartArea, scales } = chart;
    const segments = options.segments || [];

    if (!segments.length || !scales.x) return;

    ctx.save();

    segments.forEach((segment: any) => {
      // 時間をChart.jsのスケールを使って正確にピクセル位置に変換
      const startPixel = scales.x.getPixelForValue(segment.startTime);
      const endPixel = scales.x.getPixelForValue(segment.endTime);

      // Chart areaの境界内でクリッピング
      const clippedStart = Math.max(startPixel, chartArea.left);
      const clippedEnd = Math.min(endPixel, chartArea.right);

      if (clippedEnd > clippedStart) {
        ctx.fillStyle = segment.color;
        ctx.fillRect(
          clippedStart,
          chartArea.top,
          clippedEnd - clippedStart,
          chartArea.bottom - chartArea.top
        );
      }
    });

    ctx.restore();
  }
};

// Chart.jsのコンポーネントを登録
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  TimeScale, // ← 追加
  segmentBackgroundPlugin
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
  const [timeRangeMode, setTimeRangeMode] = useState<'auto' | 'race' | 'custom'>('race');
  const [offsetMinutes, setOffsetMinutes] = useState<number>(10);
  const [customTimeRange, setCustomTimeRange] = useState<TimeRange | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  // 🆕 管理者コメント関連のstate
  const [comment, setComment] = useState<string | null>(null);
  const [editedComment, setEditedComment] = useState('');
  const [isSavingComment, setIsSavingComment] = useState(false);
  const [commentError, setCommentError] = useState('');
  const [isGeneratingDraft, setIsGeneratingDraft] = useState(false);

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

  // 🆕 取得したコメントを編集用stateに同期
  useEffect(() => {
    setEditedComment(comment || '');
  }, [comment]);

  const fetchFeedbackData = async () => {
    try {
      setIsLoading(true);
      setError('');

      if (!selectedCompetition) {
        setError('大会が選択されていません');
        return;
      }

      let feedbackData;
      
      if (isAdminView && userId) {
        feedbackData = await feedbackService.getAdminUserFeedbackData(userId, selectedCompetition);
      } else {
        feedbackData = await feedbackService.getFeedbackData(selectedCompetition);
      }

      setSensorData(feedbackData.sensor_data || []);
      setRaceRecord(feedbackData.race_record);
      setComment(feedbackData.comment ?? null); // 🆕 追加

    } catch (err: any) {
      console.error('Feedback data fetch error:', err);
      setError(err.message || 'データの取得に失敗しました');
      setSensorData([]);
      setRaceRecord(null);
      setComment(null); // 🆕 追加
    } finally {
      setIsLoading(false);
    }
  };

  // 🆕 管理者コメントの保存
  const handleSaveComment = async () => {
    if (!userId || !selectedCompetition) return;

    setIsSavingComment(true);
    setCommentError('');
    try {
      await feedbackService.saveFeedbackComment(userId, selectedCompetition, editedComment);
      setComment(editedComment);
    } catch (err: any) {
      console.error('Comment save error:', err);
      setCommentError(err.message || 'コメントの保存に失敗しました');
    } finally {
      setIsSavingComment(false);
    }
  };

  const handleGenerateDraft = async () => {
    if (!userId || !selectedCompetition) return;
    setIsGeneratingDraft(true);
    setCommentError('');
    try {
      const draft = await feedbackService.generateFeedbackCommentDraft(userId, selectedCompetition);
      setEditedComment(draft);
    } catch (err: any) {
      setCommentError(err.message);
    } finally {
      setIsGeneratingDraft(false);
    }
  };

  // 時間範囲を計算（memoization）
  const timeRange = useMemo(() => {
    if (timeRangeMode === 'custom' && customTimeRange) {
      return customTimeRange;
    }

    if (timeRangeMode === 'race' && raceRecord) {
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
        endTime = new Date(new Date(raceRecord.run_start).getTime() + 60 * 60 * 1000).toISOString();
      }

      if (startTime && endTime) {
        const start = new Date(new Date(startTime).getTime() - offsetMinutes * 60 * 1000);
        const end = new Date(new Date(endTime).getTime() + offsetMinutes * 60 * 1000);
        
        return {
          start: start.toISOString(),
          end: end.toISOString()
        };
      }
    }

    // auto モード: データ全体の範囲
    if (sensorData.length > 0) {
      const timestamps = sensorData.map(d => new Date(d.timestamp));
      const minTime = new Date(Math.min(...timestamps.map(t => t.getTime())));
      const maxTime = new Date(Math.max(...timestamps.map(t => t.getTime())));
      
      return {
        start: minTime.toISOString(),
        end: maxTime.toISOString()
      };
    }

    return null;
  }, [timeRangeMode, offsetMinutes, raceRecord, sensorData, customTimeRange]);

  // チャートデータの生成（memoization）
  const chartData = useMemo(() => {
    if (!sensorData.length) return { labels: [], datasets: [] };

    let filteredData = sensorData;

    // 時間範囲でフィルタリング
    if (timeRange && timeRangeMode !== 'auto') {
      const startTime = new Date(timeRange.start);
      const endTime = new Date(timeRange.end);
      
      filteredData = sensorData.filter(data => {
        const dataTime = new Date(data.timestamp);
        return dataTime >= startTime && dataTime <= endTime;
      });
    }

    if (filteredData.length === 0) {
      return { labels: [], datasets: [] };
    }

    // time scaleではlabelsは不要、データポイントにx値を含める
    const datasets = [];

    // 体表温度（左軸）
    if (filteredData.some(point => point.skin_temperature !== undefined && point.skin_temperature !== null)) {
      const skinTempData = filteredData
        .filter(point => point.skin_temperature !== undefined && point.skin_temperature !== null)
        .map(point => ({
          x: point.timestamp,
          y: point.skin_temperature
        }))
        .sort((a, b) => new Date(a.x).getTime() - new Date(b.x).getTime()); // 時間順にソート

      datasets.push({
        label: '体表温度',
        data: skinTempData,
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        borderWidth: 2,
        tension: 0.4,
        yAxisID: 'y',
        pointRadius: 0.5,
        pointHoverRadius: 5,
        spanGaps: 5 * 60 * 1000, // 5分以内なら線をつなげる
        fill: false, // 塗りつぶしを無効化
      });
    }

    // カプセル体温度（左軸）
    if (filteredData.some(point => point.core_temperature !== undefined && point.core_temperature !== null)) {
      const coreTempData = filteredData
        .filter(point => point.core_temperature !== undefined && point.core_temperature !== null)
        .map(point => ({
          x: point.timestamp,
          y: point.core_temperature
        }))
        .sort((a, b) => new Date(a.x).getTime() - new Date(b.x).getTime());

      datasets.push({
        label: 'カプセル体温',
        data: coreTempData,
        borderColor: 'rgb(239, 68, 68)',
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
        borderWidth: 2,
        tension: 0.4,
        yAxisID: 'y',
        pointRadius: 0.5,
        pointHoverRadius: 5,
        spanGaps: 5 * 60 * 1000,
        fill: false,
      });
    }

    // WBGT温度（左軸）
    if (filteredData.some(point => point.wbgt_temperature !== undefined && point.wbgt_temperature !== null)) {
      const wbgtData = filteredData
        .filter(point => point.wbgt_temperature !== undefined && point.wbgt_temperature !== null)
        .map(point => ({
          x: point.timestamp,
          y: point.wbgt_temperature
        }))
        .sort((a, b) => new Date(a.x).getTime() - new Date(b.x).getTime());

      datasets.push({
        label: 'WBGT値',
        data: wbgtData,
        borderColor: 'rgb(245, 158, 11)',
        backgroundColor: 'rgba(245, 158, 11, 0.1)',
        borderWidth: 2,
        tension: 0.4,
        yAxisID: 'y',
        pointRadius: 0.5,
        pointHoverRadius: 5,
        spanGaps: 15 * 60 * 1000,
        fill: false,
      });
    }

    // 心拍数（右軸）
    if (filteredData.some(point => point.heart_rate !== undefined && point.heart_rate !== null)) {
      const heartRateData = filteredData
        .filter(point => point.heart_rate !== undefined && point.heart_rate !== null)
        .map(point => ({
          x: point.timestamp,
          y: point.heart_rate
        }))
        .sort((a, b) => new Date(a.x).getTime() - new Date(b.x).getTime());

      datasets.push({
        label: '心拍数',
        data: heartRateData,
        borderColor: 'rgb(34, 197, 94)',
        backgroundColor: 'rgba(34, 197, 94, 0.1)',
        borderWidth: 2,
        tension: 0.4,
        yAxisID: 'y1',
        pointRadius: 0.5,
        pointHoverRadius: 5,
        spanGaps: 5 * 60 * 1000,
        fill: false,
      });
    }

    return { labels: [], datasets }; // labelsは空配列
  }, [sensorData, timeRange, timeRangeMode]);

  // 競技区間のセグメントを計算（memoization）
  const segments = useMemo(() => {
    if (!raceRecord || timeRangeMode !== 'race') return [];

    const segmentData = [];

    // Swim区間
    if (raceRecord.swim_start) {
      const swimEnd = raceRecord.swim_finish || raceRecord.bike_start;
      
      if (swimEnd) {
        segmentData.push({
          startTime: new Date(raceRecord.swim_start).getTime(),
          endTime: new Date(swimEnd).getTime(),
          color: 'rgba(191, 219, 254, 0.3)',
          type: 'swim',
          label: 'Swim'
        });
      }
    }

    // Bike区間
    if (raceRecord.bike_start) {
      const bikeEnd = raceRecord.bike_finish || raceRecord.run_start;
      
      if (bikeEnd) {
        segmentData.push({
          startTime: new Date(raceRecord.bike_start).getTime(),
          endTime: new Date(bikeEnd).getTime(),
          color: 'rgba(254, 215, 170, 0.3)',
          type: 'bike',
          label: 'Bike'
        });
      }
    }

    // Run区間
    if (raceRecord.run_start) {
      const runEnd = raceRecord.run_finish;
      
      if (runEnd) {
        segmentData.push({
          startTime: new Date(raceRecord.run_start).getTime(),
          endTime: new Date(runEnd).getTime(),
          color: 'rgba(187, 247, 208, 0.3)',
          type: 'run',
          label: 'Run'
        });
      }
    }

    return segmentData;
  }, [raceRecord, timeRangeMode]);

  // チャートオプション（memoization）
  const chartOptions = useMemo(() => {
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
        },
        segmentBackground: {
          segments: segments
        }
      },
      scales: {
        x: {
          type: 'time' as const, // ← 重要：time scaleを使用
          time: {
            unit: 'minute' as const,
            displayFormats: {
              minute: 'HH:mm'
            }
          },
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
        mode: 'nearest' as const,
      }
    };
  }, [sensorData, segments]);

  const handleCustomTimeRangeChange = useCallback((field: 'start' | 'end', value: string) => {
    setCustomTimeRange(prev => ({
      ...prev,
      [field]: value
    } as TimeRange));
  }, []);

  // データ時間範囲の取得
  const dataTimeRange = useMemo(() => {
    if (sensorData.length === 0) return null;
    
    const timestamps = sensorData.map(d => new Date(d.timestamp));
    const minTime = new Date(Math.min(...timestamps.map(t => t.getTime())));
    const maxTime = new Date(Math.max(...timestamps.map(t => t.getTime())));
    
    return {
      start: minTime.toISOString().slice(0, 16),
      end: maxTime.toISOString().slice(0, 16)
    };
  }, [sensorData]);

  return (
    <div className={`bg-white p-6 rounded-lg shadow-md ${className}`}>
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
              <label className="text-sm font-medium text-gray-700">表示範囲:</label>
              <select
                value={timeRangeMode}
                onChange={(e) => setTimeRangeMode(e.target.value as 'auto' | 'race' | 'custom')}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="race">大会記録ベース</option>
                <option value="auto">自動</option>
                <option value="custom">カスタム</option>
              </select>
            </div>

            {/* オフセット調整（大会記録ベースの場合） */}
            {timeRangeMode === 'race' && (
              <div className="flex items-center gap-2">
                <label className="text-sm font-medium text-gray-700">前後:</label>
                <input
                  type="range"
                  min="0"
                  max="60"
                  value={offsetMinutes}
                  onChange={(e) => setOffsetMinutes(Number(e.target.value))}
                  className="w-20"
                />
                <span className="text-sm text-gray-600 min-w-[50px]">{offsetMinutes}分</span>
              </div>
            )}
          </div>
        </div>

        {/* カスタム時間範囲入力 */}
        {timeRangeMode === 'custom' && dataTimeRange && (
          <div className="flex gap-4 items-center bg-gray-50 p-3 rounded-md">
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium text-gray-700">開始:</label>
              <input
                type="datetime-local"
                value={customTimeRange?.start?.slice(0, 16) || dataTimeRange.start}
                onChange={(e) => handleCustomTimeRangeChange('start', e.target.value + ':00.000Z')}
                min={dataTimeRange.start}
                max={dataTimeRange.end}
                className="px-2 py-1 border border-gray-300 rounded text-sm"
              />
            </div>
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium text-gray-700">終了:</label>
              <input
                type="datetime-local"
                value={customTimeRange?.end?.slice(0, 16) || dataTimeRange.end}
                onChange={(e) => handleCustomTimeRangeChange('end', e.target.value + ':00.000Z')}
                min={dataTimeRange.start}
                max={dataTimeRange.end}
                className="px-2 py-1 border border-gray-300 rounded text-sm"
              />
            </div>
          </div>
        )}

        {/* エラー表示 */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        )}

        {/* チャート表示エリア */}
        <div className="relative" style={{ height: `${height}px` }}>
          {isLoading ? (
            <div className="absolute inset-0 flex justify-center items-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : !selectedCompetition ? (
            <div className="absolute inset-0 flex justify-center items-center">
              <div className="text-center text-gray-500">
                <p className="text-lg font-medium">大会を選択してください</p>
              </div>
            </div>
          ) : sensorData.length === 0 ? (
            <div className="absolute inset-0 flex justify-center items-center">
              <div className="text-center text-gray-500">
                <p className="text-lg font-medium">表示するデータがありません</p>
              </div>
            </div>
          ) : (
            <div className="h-full">
              <Line data={chartData} options={chartOptions} />
            </div>
          )}
        </div>

        {/* データ情報 */}
        {sensorData.length > 0 && selectedCompetition && (
          <div className="flex justify-between text-sm text-gray-500">
            <span>
              {chartData.datasets.reduce((total, dataset) => total + dataset.data.length, 0)}/{sensorData.length}件のデータポイントを表示中
            </span>
            {timeRange && (
              <span>
                表示範囲: {new Date(timeRange.start).toLocaleString('ja-JP')} 
                〜 {new Date(timeRange.end).toLocaleString('ja-JP')}
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

        {/* 🆕 管理者コメント（管理者ビュー：編集可能） */}
        {isAdminView && selectedCompetition && (
          <div className="mt-2 border-t pt-4">
            <label className="label">管理者コメント</label>
            <textarea
              value={editedComment}
              onChange={(e) => setEditedComment(e.target.value)}
              rows={4}
              className="input"
              placeholder="例：Bike区間（10:15頃）で体表温が急上昇しています。給水タイミングを見直しましょう。"
            />
            {commentError && <p className="form-error">{commentError}</p>}
            <div className="flex gap-2 mt-2">
              <button
                onClick={handleGenerateDraft}
                disabled={isGeneratingDraft}
                className="btn btn-outline btn-sm"
              >
                {isGeneratingDraft ? '生成中...' : '🤖 AIコメント案を生成'}
              </button>
              <button
                onClick={handleSaveComment}
                disabled={isSavingComment}
                className="btn btn-primary btn-sm"
              >
                {isSavingComment ? '保存中...' : 'コメントを保存'}
              </button>
            </div>
          </div>
        )}

        {/* 🆕 管理者コメント（ユーザービュー：読み取り専用） */}
        {!isAdminView && comment && (
          <div className="alert alert-info">
            <p className="text-sm font-semibold" style={{ marginBottom: 'var(--spacing-1)' }}>
              コーチからのコメント
            </p>
            <p className="text-sm whitespace-pre-wrap">{comment}</p>
          </div>
        )}
      </div>
    </div>
  );
};