// src/services/feedbackService.ts

import { api } from './api';

export interface CompetitionRace {
  id: string;
  name: string;
  date: string;
}

export interface SensorDataPoint {
  timestamp: string;
  skin_temperature?: number;
  core_temperature?: number;
  wbgt_temperature?: number;
  heart_rate?: number;
}

export interface RaceRecord {
  swim_start?: string;
  swim_finish?: string;
  bike_start?: string;
  bike_finish?: string;
  run_start?: string;
  run_finish?: string;
}

export interface FeedbackDataResponse {
  sensor_data: SensorDataPoint[];
  race_record: RaceRecord | null;
  competition: CompetitionRace;
}

export const feedbackService = {
  // ユーザーの参加大会一覧を取得
  async getUserCompetitions(): Promise<CompetitionRace[]> {
    try {
      const response = await api.get('/me/competitions');
      return response.data || [];
    } catch (error) {
      console.error('Error fetching user competitions:', error);
      return [];
    }
  },

  // 指定された大会のフィードバックデータを取得
  async getFeedbackData(competitionId: string): Promise<FeedbackDataResponse> {
    try {
      const response = await api.get(`/me/feedback-data/${competitionId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching feedback data:', error);
      throw new Error('フィードバックデータの取得に失敗しました');
    }
  },

  // センサーデータのみを取得
  async getSensorData(competitionId: string, params?: {
    start_date?: string;
    end_date?: string;
  }): Promise<SensorDataPoint[]> {
    try {
      const queryParams = new URLSearchParams();
      queryParams.append('competition_id', competitionId);
      
      if (params?.start_date) {
        queryParams.append('start_date', params.start_date);
      }
      if (params?.end_date) {
        queryParams.append('end_date', params.end_date);
      }

      console.log('Making request to:', `/me/sensor-data?${queryParams.toString()}`);
      const response = await api.get(`/me/sensor-data?${queryParams.toString()}`);
      return response.data || [];
    } catch (error: any) {
      console.error('Error fetching sensor data:', error);
      if (error.response?.status === 403) {
        throw new Error('センサーデータへのアクセスが拒否されました。ログインし直してください。');
      }
      return [];
    }
  },

  // 大会記録データのみを取得
  async getRaceRecord(competitionId: string): Promise<RaceRecord | null> {
    try {
      const response = await api.get(`/me/race-records/${competitionId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching race record:', error);
      return null;
    }
  },

  // 管理者用：指定ユーザーの大会一覧を取得
  async getAdminUserCompetitions(userId: string): Promise<CompetitionRace[]> {
    try {
      const response = await api.get(`/admin/users/${userId}/competitions`);
      return response.data || [];
    } catch (error) {
      console.error('Error fetching admin user competitions:', error);
      return [];
    }
  },

  // 管理者用：指定ユーザーの大会データを取得
  async getAdminUserFeedbackData(userId: string, competitionId: string): Promise<FeedbackDataResponse> {
    try {
      const response = await api.get(`/admin/users/${userId}/feedback-data/${competitionId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching admin feedback data:', error);
      throw new Error('管理者用フィードバックデータの取得に失敗しました');
    }
  },
};