export interface UserSensorSummary {
  sensor_type: string;
  total_records: number;
  latest_timestamp?: string;
  sensor_id: string;
}

export interface CompetitionDetail {
  competition_id: string;
  name: string;
  date?: string;
  location?: string;
  mapped_sensors: UserSensorSummary[];
  total_records: number;
  has_race_record: boolean;
}

export interface UserDataSummary {
  total_records: number;
  total_competitions: number;
  mapped_sensor_types: string[];
  competitions: CompetitionDetail[];
  latest_data_date?: string;
}