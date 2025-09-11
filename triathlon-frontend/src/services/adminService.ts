/**
 * services/adminService.ts (新システム版)
 */

import { api } from './api';

// === 型定義 ===
export interface UserInfo {
  id: number;
  user_id: string;
  username: string;
  full_name: string;
  email: string;
  is_active: boolean;
  created_at: string;
  sensor_count: number;
  last_data_at?: string;
}

export interface UserFormData {
  user_id: string;
  username: string;
  full_name: string;
  email: string;
  password?: string;
  is_active: boolean;
}

export interface CompetitionInfo {
  id: number;
  competition_id: string;
  name: string;
  date?: string;
  location?: string;
  description?: string;
  is_active: boolean;
  created_at: string;
  participant_count?: number;
  sensor_data_count?: number;
}

export interface SystemStats {
  total_users: number;
  active_users: number;
  total_competitions: number;
  active_competitions: number;
  total_sensor_records: number;
  mapped_sensor_records: number;
  unmapped_sensor_records: number;
}

// === 🆕 マルチセンサー関連の型 ===
export interface UnmappedDataSummary {
  total_unmapped_records: number;
  by_sensor_type: Record<string, {
    total_records: number;
    unique_sensors: number;
    sensor_ids: string[];
  }>;
  competition_id?: string;
}

export interface SensorUploadResponse {
  status: string;
  batch_id: string;
  sensor_type: string;
  processed_records: number;
  errors: string[];
  message: string;
}

export interface MappingResponse {
  status: string;
  mapped_records: number;
  specialized_records: number;
  mapping_errors: string[];
  specialized_errors: string[];
  message: string;
}

export const adminService = {
  // === ユーザー管理 ===
  async getUsers(skip = 0, limit = 100, search?: string): Promise<UserInfo[]> {
    const response = await api.get<UserInfo[]>('/admin/users', {
      params: { skip, limit, search }
    });
    return response.data;
  },

  async createUser(userData: UserFormData): Promise<UserInfo> {
    const response = await api.post<UserInfo>('/admin/users', userData);
    return response.data;
  },

  async updateUser(userId: string, userData: Partial<UserFormData>): Promise<UserInfo> {
    const response = await api.put<UserInfo>(`/admin/users/${userId}`, userData);
    return response.data;
  },

  async deleteUser(userId: string): Promise<{ message: string }> {
    const response = await api.delete(`/admin/users/${userId}`);
    return response.data;
  },

  // === 大会管理 ===
  async getCompetitions(activeOnly = false): Promise<CompetitionInfo[]> {
    const response = await api.get<CompetitionInfo[]>('/admin/competitions', {
      params: { active_only: activeOnly }
    });
    return response.data;
  },

  // === システム統計 ===
  async getSystemStats(): Promise<SystemStats> {
    const response = await api.get<SystemStats>('/admin/stats');
    return response.data;
  },

  // === 🆕 マルチセンサー機能 ===
  
  // 未マッピングデータサマリー取得
  async getUnmappedDataSummary(competitionId?: string): Promise<UnmappedDataSummary> {
    const response = await api.get<UnmappedDataSummary>('/api/multi-sensor/unmapped-summary', {
      params: competitionId ? { competition_id: competitionId } : {}
    });
    return response.data;
  },

  // センサーデータアップロード（種別ごと）
  async uploadSensorData(
    sensorType: 'skin-temperature' | 'core-temperature' | 'heart-rate' | 'wbgt',
    dataFile: File,
    competitionId?: string
  ): Promise<SensorUploadResponse> {
    const formData = new FormData();
    formData.append('data_file', dataFile);
    if (competitionId) {
      formData.append('competition_id', competitionId);
    }

    const response = await api.post<SensorUploadResponse>(
      `/api/multi-sensor/upload/${sensorType}`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );

    return response.data;
  },

  // センサーマッピング適用
  async applySensorMapping(
    sensorType: 'skin-temperature' | 'core-temperature' | 'heart-rate',
    mappingFile: File,
    competitionId?: string
  ): Promise<MappingResponse> {
    const formData = new FormData();
    formData.append('mapping_file', mappingFile);
    if (competitionId) {
      formData.append('competition_id', competitionId);
    }

    const response = await api.post<MappingResponse>(
      `/api/multi-sensor/mapping/${sensorType}`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );

    return response.data;
  }
};