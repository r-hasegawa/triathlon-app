export interface UserStats {
  sensor_count: number;
  total_records: number;
  last_data_at: string | null;
  avg_temperature: number | null;
  min_temperature: number | null;
  max_temperature: number | null;
  first_data_at: string | null;
}

export interface UserWithStats extends UserInfo {
  stats?: UserStats;
}

export interface DashboardStats {
  total_users: number;
  active_users: number;
  inactive_users: number;
  total_sensors: number;
  total_data_records: number;
  users_with_data: number;
  users_without_data: number;
  recent_data_count: number;
  recent_uploads: number;
  avg_sensors_per_user: number;
  avg_records_per_user: number;
}