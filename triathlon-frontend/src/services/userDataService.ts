import api from './api';
import { UserDataSummary } from '../types/userData';

export const userDataService = {
  async getUserDataSummary(): Promise<UserDataSummary> {
    const response = await api.get('/me/data-summary');
    return response.data;
  },

  async getCompetitionData(competitionId: string, sensorType?: string) {
    const params = sensorType ? { sensor_type: sensorType } : {};
    const response = await api.get(`/me/competition/${competitionId}/sensor-data`, { params });
    return response.data;
  }
};