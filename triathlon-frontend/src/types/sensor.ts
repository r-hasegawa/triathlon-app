export interface SensorData {
  id: number;
  sensor_id: string;
  sensor_type: string;
  timestamp: string;
  temperature?: number;
  heart_rate?: number;
  value: number;
  user_id?: string;
  competition_id: string;
  created_at: string;
}

export interface SensorMapping {
  id: number;
  sensor_id: string;
  sensor_type: string;
  user_id: string;
  competition_id: string;
  created_at: string;
}

export interface Competition {
  id: number;
  competition_id: string;
  name: string;
  date: string | null;
  location: string | null;
  description: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string | null;
}

export interface User {
  id: number;
  user_id: string;
  username: string;
  full_name: string;
  email: string;
  is_active: boolean;
  created_at: string;
}

export interface Admin {
  id: number;
  admin_id: string;
  username: string;
  full_name: string;
  email: string;
  is_active: boolean;
  created_at: string;
}