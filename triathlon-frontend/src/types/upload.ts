// triathlon-frontend/src/types/upload.ts (修正版)

export interface Competition {
  competition_id: string;
  name: string;
  date: string;
  location: string;
  description?: string;
}

export interface UploadBatch {
  batch_id: string;
  sensor_type: string;
  file_name: string;
  total_records: number;
  success_records: number;
  failed_records: number;
  status: string;
  uploaded_at: string;
  uploaded_by: string;
  competition_id: string;
  error_message?: string;
}

export interface UploadResult {
  file: string;
  batch_id?: string;
  total?: number;
  success?: number;
  failed?: number;
  status: string;
  error?: string;
  sensor_ids?: string[];
  trackpoints_total?: number;
  sensors_found?: number;
}

export interface SkinTemperatureData {
  id: number;
  halshare_wearer_name: string;
  halshare_id: string;
  datetime: string;
  temperature: number;
  upload_batch_id: string;
  competition_id: string;
  mapped_user_id?: string;
}

export interface CoreTemperatureData {
  id: number;
  capsule_id: string;
  monitor_id: string;
  datetime: string;
  temperature?: number;
  status?: string;
  upload_batch_id: string;
  competition_id: string;
  mapped_user_id?: string;
}

export interface HeartRateData {
  id: number;
  sensor_id: string;
  time: string;
  heart_rate?: number;
  upload_batch_id: string;
  competition_id: string;
  mapped_user_id?: string;
}

// 🆕 修正: 不要フィールド削除、upload_batch_id追加
export interface SensorMapping {
  id: number;
  user_id: string;
  competition_id: string;
  sensor_id: string;
  sensor_type: string;
  upload_batch_id?: string;  // 🆕 追加
  created_at: string;
}

export type SensorType = 'skin_temperature' | 'core_temperature' | 'heart_rate' | 'wbgt' | 'other';
export type UploadStatus = 'success' | 'failed' | 'partial';