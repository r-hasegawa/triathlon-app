import api from './api';

export interface UploadResponse {
  message: string;
  sensor_data: {
    processed_records: number;
    errors: string[];
    total_errors: number;
  };
  sensor_mapping: {
    processed_records: number;
    errors: string[];
    total_errors: number;
  };
  upload_ids: {
    sensor_data: string;
    sensor_mapping: string;
  };
}

export interface UploadHistory {
  upload_id: string;
  filename: string;
  status: 'pending' | 'processing' | 'completed' | 'completed_with_errors' | 'failed';
  records_count: number;
  file_size: number;
  uploaded_at: string;
  processed_at: string | null;
  error_message: string | null;
}

export interface UserInfo {
  id: number;
  user_id: string;
  username: string;
  full_name: string | null;
  email: string | null;
  is_active: boolean;
  created_at: string;
  sensor_count?: number;
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

export interface UserStats {
  sensor_count: number;
  total_records: number;
  last_data_at: string | null;
  avg_temperature: number | null;
  min_temperature: number | null;
  max_temperature: number | null;
  first_data_at: string | null;
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

export const adminService = {
  // CSVアップロード
  async uploadCSVFiles(sensorDataFile: File, mappingFile: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('sensor_data_file', sensorDataFile);
    formData.append('sensor_mapping_file', mappingFile);

    const response = await api.post<UploadResponse>('/admin/upload/csv', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  },

  // アップロード履歴取得
  async getUploadHistory(skip = 0, limit = 50): Promise<UploadHistory[]> {
    const response = await api.get<UploadHistory[]>('/admin/upload-history', {
      params: { skip, limit }
    });
    return response.data;
  },

  // ユーザー一覧取得（基本）
  async getUsers(skip = 0, limit = 100, search?: string): Promise<UserInfo[]> {
    const response = await api.get<UserInfo[]>('/admin/users', {
      params: { skip, limit, search }
    });
    return response.data;
  },

  // ユーザー一覧取得（統計情報付き）
  async getUsersWithStats(skip = 0, limit = 1000, search?: string): Promise<UserInfo[]> {
    const response = await api.get<UserInfo[]>('/admin/users-with-stats', {
      params: { skip, limit, search }
    });
    return response.data;
  },

  // ユーザー作成
  async createUser(userData: UserFormData): Promise<UserInfo> {
    const response = await api.post<UserInfo>('/admin/users', userData);
    return response.data;
  },

  // ユーザー更新
  async updateUser(userId: string, userData: Partial<UserFormData>): Promise<UserInfo> {
    const response = await api.put<UserInfo>(`/admin/users/${userId}`, userData);
    return response.data;
  },

  // ユーザー削除
  async deleteUser(userId: string): Promise<void> {
    await api.delete(`/admin/users/${userId}`);
  },

  // パスワードリセット
  async resetUserPassword(userId: string, newPassword: string): Promise<void> {
    await api.post(`/admin/users/${userId}/reset-password`, {
      new_password: newPassword
    });
  },
  
  // ユーザーの詳細統計取得
  async getUserStats(userId: string): Promise<UserStats> {
    const response = await api.get<UserStats>(`/admin/users/${userId}/stats`);
    return response.data;
  },

  // 管理者ダッシュボード統計
  async getDashboardStats(): Promise<DashboardStats> {
    const response = await api.get<DashboardStats>('/admin/dashboard-stats');
    return response.data;
  }
};