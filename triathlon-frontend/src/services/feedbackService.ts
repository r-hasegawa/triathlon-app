// src/services/feedbackService.ts - 修正版

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

  // 指定された大会のフィードバックデータを取得（統合API使用）
  async getFeedbackData(competitionId: string): Promise<FeedbackDataResponse> {
    try {
      const response = await api.get(`/me/feedback-data/${competitionId}`);
      
      return {
        sensor_data: response.data.sensor_data || [],
        race_record: response.data.race_record || null,
        competition: response.data.competition || {
          id: competitionId,
          name: 'Unknown Competition',
          date: new Date().toISOString()
        }
      };
    } catch (error: any) {
      console.error('Error fetching feedback data:', error);
      console.error('Error details:', error.response?.data);
      throw new Error('フィードバックデータの取得に失敗しました');
    }
  },

  // センサーデータのみを取得（互換性のため残すが、統合APIを推奨）
  async getSensorData(competitionId: string, params?: {
    start_date?: string;
    end_date?: string;
  }): Promise<SensorDataPoint[]> {
    try {
      // 統合APIからセンサーデータのみを抽出
      const feedbackData = await this.getFeedbackData(competitionId);
      return feedbackData.sensor_data;
    } catch (error) {
      console.error('Error fetching sensor data:', error);
      return [];
    }
  },

  // 大会記録のみを取得（互換性のため残すが、統合APIを推奨）
  async getRaceRecord(competitionId: string): Promise<RaceRecord | null> {
    try {
      // 統合APIから大会記録のみを抽出
      const feedbackData = await this.getFeedbackData(competitionId);
      return feedbackData.race_record;
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
      
      return {
        sensor_data: response.data.sensor_data || [],
        race_record: response.data.race_record || null,
        competition: response.data.competition || {
          id: competitionId,
          name: 'Unknown Competition',
          date: new Date().toISOString()
        }
      };
    } catch (error: any) {
      console.error('Error fetching admin feedback data:', error);
      console.error('Error details:', error.response?.data);
      throw new Error('管理者用フィードbackックデータの取得に失敗しました');
    }
  },
};