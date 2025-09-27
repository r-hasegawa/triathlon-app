// src/types/feedback.ts

export interface CompetitionRace {
  id: string;
  name: string;
  date: string;
  description?: string;
}

export interface SensorDataPoint {
  timestamp: string;
  skin_temperature?: number;
  core_temperature?: number;
  wbgt_temperature?: number;
  heart_rate?: number;
  sensor_id?: string;
  data_type?: 'skin_temperature' | 'core_temperature' | 'wbgt' | 'heart_rate';
}

export interface RaceRecord {
  competition_id: string;
  user_id: string;
  // Swim区間
  swim_start?: string;
  swim_finish?: string;
  // Bike区間  
  bike_start?: string;
  bike_finish?: string;
  // Run区間
  run_start?: string;
  run_finish?: string;
  // LAP記録（可変数）
  lap_records?: LapRecord[];
}

export interface LapRecord {
  lap_number: number;
  lap_time: string;
  split_time?: string;
  segment_type?: 'swim' | 'bike' | 'run';
}

export interface FeedbackDataResponse {
  sensor_data: SensorDataPoint[];
  race_record: RaceRecord | null;
  competition: CompetitionRace;
  statistics?: {
    total_records: number;
    date_range: {
      start: string;
      end: string;
    };
    data_types: string[];
  };
}

export interface FeedbackChartSegment {
  start: number; // timestamp
  end: number;   // timestamp
  color: string;
  type: 'swim' | 'bike' | 'run';
  label: string;
}

export interface ChartTimeRange {
  start: string; // ISO string
  end: string;   // ISO string
}

// APIリクエスト用の型
export interface FeedbackDataRequest {
  competition_id: string;
  user_id?: string; // 管理者用
  offset_minutes?: number;
  include_race_records?: boolean;
}

export interface SensorDataQuery {
  competition_id?: string;
  start_date?: string;
  end_date?: string;
  data_types?: ('skin_temperature' | 'core_temperature' | 'wbgt' | 'heart_rate')[];
  sensor_ids?: string[];
}