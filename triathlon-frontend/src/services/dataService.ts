import api from './api';
import { SensorData, SensorMapping, SensorDataStats, ChartDataPoint } from '@/types/sensor';

export const dataService = {
  async getMySensors(): Promise<SensorMapping[]> {
    const response = await api.get<SensorMapping[]>('/data/my-sensors');
    return response.data;
  },

  async getMyDataStats(params?: {
    sensor_id?: string;
    start_date?: string;
    end_date?: string;
  }): Promise<SensorDataStats> {
    const response = await api.get<SensorDataStats>('/data/my-data/stats', { params });
    return response.data;
  },

  async getMyData(params?: {
    sensor_id?: string;
    start_date?: string;
    end_date?: string;
    page?: number;
    limit?: number;
    order?: 'asc' | 'desc';
  }): Promise<{ data: SensorData[]; total: number; page: number; limit: number; has_next: boolean }> {
    const response = await api.get('/data/my-data', { params });
    return response.data;
  },

  async getChartData(params?: {
    sensor_id?: string;
    start_date?: string;
    end_date?: string;
    interval?: '1min' | '5min' | '15min' | '1hour' | '1day';
  }): Promise<{ data: ChartDataPoint[]; total_points: number }> {
    const response = await api.get('/data/my-data/chart', { params });
    return response.data;
  },

  async exportData(format: 'csv' | 'json', params?: {
    sensor_id?: string;
    start_date?: string;
    end_date?: string;
  }): Promise<Blob> {
    const response = await api.get('/data/my-data/export', {
      params: { ...params, format },
      responseType: 'blob',
    });
    return response.data;
  }
};