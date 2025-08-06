export interface SensorData {
  id: number;
  sensor_id: string;
  user_id: string;
  timestamp: string;
  temperature: number;
  created_at: string;
}

export interface SensorMapping {
  id: number;
  sensor_id: string;
  user_id: string;
  subject_name: string | null;
  device_type: string;
  is_active: boolean;
  created_at: string;
}

export interface SensorDataStats {
  total_records: number;
  min_temperature: number | null;
  max_temperature: number | null;
  avg_temperature: number | null;
  start_time: string | null;
  end_time: string | null;
}

export interface ChartDataPoint {
  timestamp: string;
  temperature: number;
  sensor_id: string;
}