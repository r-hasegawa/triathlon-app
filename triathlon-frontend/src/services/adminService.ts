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

export interface MultipleUploadResponse {
  message: string;
  mapping_file: {
    filename: string;
    records_processed: number;
    errors: string[];
  };
  data_files: Array<{
    filename: string;
    records_processed: number;
    errors: string[];
  }>;
  summary: {
    total_files_processed: number;
    total_records_processed: number;
    total_errors: number;
    files_with_errors: number;
  };
  errors: string[];
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

  // 複数CSVアップロード
  async uploadMultipleCSVFiles(sensorDataFiles: File[], mappingFile: File): Promise<MultipleUploadResponse> {
    const formData = new FormData();
    
    // 複数のデータファイルを追加
    sensorDataFiles.forEach(file => {
      formData.append('sensor_data_files', file);
    });
    
    // マッピングファイルを追加
    formData.append('sensor_mapping_file', mappingFile);

    const response = await api.post<MultipleUploadResponse>('/admin/upload-multiple-csv', formData, {
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
  },

  /**
   * 特定ユーザーのセンサデータを取得（管理者権限）
   */
  async getUserData(
    userId: string, 
    params?: {
      sensorId?: string;
      startDate?: string;
      endDate?: string;
      page?: number;
      limit?: number;
      order?: 'asc' | 'desc';
    }
  ) {
    const queryParams = new URLSearchParams();
    if (params?.sensorId) queryParams.append('sensor_id', params.sensorId);
    if (params?.startDate) queryParams.append('start_date', params.startDate);
    if (params?.endDate) queryParams.append('end_date', params.endDate);
    if (params?.page !== undefined) queryParams.append('page', params.page.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.order) queryParams.append('order', params.order);

    const response = await api.get(`/admin/users/${userId}/data?${queryParams}`);
    return response.data;
  },

  /**
   * 特定ユーザーのセンサー一覧を取得（管理者権限）
   */
  async getUserSensors(userId: string) {
    const response = await api.get(`/admin/users/${userId}/sensors`);
    return response.data;
  },

  // === 🆕 大会管理機能 ===

  /**
   * 大会一覧を取得（管理者権限）
   */
  async getCompetitions(includeInactive: boolean = false) {
    const response = await api.get('/api/competitions/', {
      params: { include_inactive: includeInactive }
    });
    return response.data;
  },

  /**
   * 新規大会を作成（管理者権限）
   */
  async createCompetition(competitionData: {
    name: string;
    date?: string | null;
    location?: string | null;
    description?: string | null;
  }) {
    const response = await api.post('/api/competitions/', competitionData);
    return response.data;
  },

  /**
   * 大会情報を更新（管理者権限）
   */
  async updateCompetition(competitionId: string, competitionData: {
    name?: string;
    date?: string | null;
    location?: string | null;
    description?: string | null;
    is_active?: boolean;
  }) {
    const response = await api.put(`/api/competitions/${competitionId}`, competitionData);
    return response.data;
  },

  /**
   * 大会を削除（管理者権限）
   */
  async deleteCompetition(competitionId: string) {
    const response = await api.delete(`/api/competitions/${competitionId}`);
    return response.data;
  },

  /**
   * 大会の詳細情報を取得
   */
  async getCompetitionDetail(competitionId: string) {
    const response = await api.get(`/api/competitions/${competitionId}`);
    return response.data;
  }

  // ✅ 重複していた getUserStats を削除済み
};