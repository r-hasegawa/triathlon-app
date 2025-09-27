// src/services/userDataService.ts

import { api } from './api';

export interface UserDataSummary {
  total_sensor_records: number;
  competitions_participated: number;
  avg_temperature: number | null;
  max_temperature: number | null;
  min_temperature: number | null;
  latest_data_date: string | null;
}

export interface SensorDataStats {
  total_records: number;
  avg_temperature: number | null;
  max_temperature: number | null;
  min_temperature: number | null;
  latest_record_date: string | null;
  earliest_record_date: string | null;
}

export interface SensorMapping {
  sensor_id: string;
  subject_name?: string;
  sensor_type?: string;
  competition_id?: string;
}

export interface ChartDataPoint {
  timestamp: string;
  temperature: number;
  sensor_id?: string;
}

export interface ChartDataParams {
  sensor_id?: string;
  start_date: string;
  end_date: string;
  interval: '1min' | '5min' | '15min' | '1hour' | '1day';
}

export interface ChartDataResponse {
  data: ChartDataPoint[];
  total_count: number;
  date_range: {
    start: string;
    end: string;
  };
}

export const userDataService = {
  // ユーザーのデータサマリーを取得
  async getUserDataSummary(): Promise<UserDataSummary> {
    const response = await api.get('/me/data-summary');
    return response.data;
  },

  // ユーザーのセンサー統計を取得
  async getUserStats(): Promise<SensorDataStats> {
    const response = await api.get('/me/stats');
    return response.data;
  },

  // ユーザーのセンサーマッピング一覧を取得
  async getUserSensorMappings(): Promise<SensorMapping[]> {
    const response = await api.get('/me/sensor-mappings');
    return response.data || [];
  },

  // チャート用データを取得
  async getChartData(params: ChartDataParams): Promise<ChartDataResponse> {
    const queryParams = new URLSearchParams({
      start_date: params.start_date,
      end_date: params.end_date,
      interval: params.interval,
    });

    if (params.sensor_id) {
      queryParams.append('sensor_id', params.sensor_id);
    }

    const response = await api.get(`/me/chart-data?${queryParams.toString()}`);
    return response.data;
  },

  // センサーデータの詳細を取得（ページネーション対応）
  async getSensorDataDetails(params: {
    page?: number;
    page_size?: number;
    sensor_id?: string;
    start_date?: string;
    end_date?: string;
    data_type?: string;
  } = {}) {
    const queryParams = new URLSearchParams();
    
    if (params.page !== undefined) {
      queryParams.append('page', params.page.toString());
    }
    if (params.page_size !== undefined) {
      queryParams.append('page_size', params.page_size.toString());
    }
    if (params.sensor_id) {
      queryParams.append('sensor_id', params.sensor_id);
    }
    if (params.start_date) {
      queryParams.append('start_date', params.start_date);
    }
    if (params.end_date) {
      queryParams.append('end_date', params.end_date);
    }
    if (params.data_type) {
      queryParams.append('data_type', params.data_type);
    }

    const response = await api.get(`/me/sensor-data-details?${queryParams.toString()}`);
    return response.data;
  },

  // ユーザーのセンサーデータをエクスポート
  async exportSensorData(params: {
    format: 'csv' | 'json';
    sensor_id?: string;
    start_date?: string;
    end_date?: string;
    data_type?: string;
  }): Promise<Blob> {
    const queryParams = new URLSearchParams({
      format: params.format,
    });

    if (params.sensor_id) {
      queryParams.append('sensor_id', params.sensor_id);
    }
    if (params.start_date) {
      queryParams.append('start_date', params.start_date);
    }
    if (params.end_date) {
      queryParams.append('end_date', params.end_date);
    }
    if (params.data_type) {
      queryParams.append('data_type', params.data_type);
    }

    const response = await fetch(`${api.defaults.baseURL}/me/export-sensor-data?${queryParams.toString()}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
      },
    });

    if (!response.ok) {
      throw new Error('データのエクスポートに失敗しました');
    }

    return response.blob();
  },

  // データの更新通知を取得
  async getDataUpdates(): Promise<{
    last_update: string;
    pending_uploads: number;
    recent_competitions: Array<{
      id: string;
      name: string;
      date: string;
    }>;
  }> {
    const response = await api.get('/me/data-updates');
    return response.data;
  },

  // ユーザー設定を取得
  async getUserPreferences(): Promise<{
    chart_default_range: string;
    temperature_unit: 'celsius' | 'fahrenheit';
    timezone: string;
    notification_enabled: boolean;
  }> {
    const response = await api.get('/me/preferences');
    return response.data;
  },

  // ユーザー設定を更新
  async updateUserPreferences(preferences: {
    chart_default_range?: string;
    temperature_unit?: 'celsius' | 'fahrenheit';
    timezone?: string;
    notification_enabled?: boolean;
  }): Promise<void> {
    await api.put('/me/preferences', preferences);
  },

  // データ品質レポートを取得
  async getDataQualityReport(): Promise<{
    total_records: number;
    quality_score: number;
    issues: Array<{
      type: string;
      count: number;
      description: string;
    }>;
    missing_data_periods: Array<{
      start: string;
      end: string;
      data_type: string;
    }>;
  }> {
    const response = await api.get('/me/data-quality');
    return response.data;
  },

  // 特定の大会のデータサマリーを取得
  async getCompetitionDataSummary(competitionId: string): Promise<{
    competition_id: string;
    competition_name: string;
    participation_date: string;
    total_records: number;
    data_types: string[];
    duration: {
      start: string;
      end: string;
      total_minutes: number;
    };
    statistics: {
      avg_temperature: number | null;
      max_temperature: number | null;
      min_temperature: number | null;
      avg_heart_rate: number | null;
      max_heart_rate: number | null;
    };
  }> {
    const response = await api.get(`/me/competitions/${competitionId}/summary`);
    return response.data;
  },
};