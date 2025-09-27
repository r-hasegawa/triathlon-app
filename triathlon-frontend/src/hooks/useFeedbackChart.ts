// src/hooks/useFeedbackChart.ts

import { useState, useEffect, useCallback } from 'react';
import { 
  feedbackService, 
  type CompetitionRace, 
  type SensorDataPoint, 
  type RaceRecord 
} from '@/services/feedbackService';

interface UseFeedbackChartProps {
  userId?: string;
  isAdminView?: boolean;
  defaultCompetitionId?: string;
}

export const useFeedbackChart = ({
  userId,
  isAdminView = false,
  defaultCompetitionId,
}: UseFeedbackChartProps = {}) => {
  const [competitions, setCompetitions] = useState<CompetitionRace[]>([]);
  const [selectedCompetition, setSelectedCompetition] = useState<string>(
    defaultCompetitionId || ''
  );
  const [sensorData, setSensorData] = useState<SensorDataPoint[]>([]);
  const [raceRecord, setRaceRecord] = useState<RaceRecord | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  // 大会一覧を取得
  const fetchCompetitions = useCallback(async () => {
    try {
      setError('');
      let data: CompetitionRace[];
      
      if (isAdminView && userId) {
        data = await feedbackService.getAdminUserCompetitions(userId);
      } else {
        data = await feedbackService.getUserCompetitions();
      }
      
      setCompetitions(data);
      
      // デフォルト大会が指定されていない場合、最新の大会を選択
      if (!defaultCompetitionId && data.length > 0) {
        const latestCompetition = data.reduce((latest, comp) => 
          new Date(comp.date) > new Date(latest.date) ? comp : latest
        );
        setSelectedCompetition(latestCompetition.id);
      }
    } catch (err: any) {
      console.error('Competitions fetch error:', err);
      setError('大会一覧の取得に失敗しました');
    }
  }, [userId, isAdminView, defaultCompetitionId]);

  // フィードバックデータを取得
  const fetchFeedbackData = useCallback(async (competitionId: string) => {
    if (!competitionId) return;

    try {
      setIsLoading(true);
      setError('');

      let response;
      if (isAdminView && userId) {
        response = await feedbackService.getAdminUserFeedbackData(userId, competitionId);
      } else {
        response = await feedbackService.getFeedbackData(competitionId);
      }

      setSensorData(response.sensor_data || []);
      setRaceRecord(response.race_record || null);

    } catch (err: any) {
      console.error('Feedback data fetch error:', err);
      setError(err.message || 'フィードバックデータの取得に失敗しました');
      setSensorData([]);
      setRaceRecord(null);
    } finally {
      setIsLoading(false);
    }
  }, [userId, isAdminView]);

  // 選択された大会が変更されたらデータを取得
  useEffect(() => {
    if (selectedCompetition) {
      fetchFeedbackData(selectedCompetition);
    }
  }, [selectedCompetition, fetchFeedbackData]);

  // 初期化時に大会一覧を取得
  useEffect(() => {
    fetchCompetitions();
  }, [fetchCompetitions]);

  const refreshData = useCallback(() => {
    if (selectedCompetition) {
      fetchFeedbackData(selectedCompetition);
    }
  }, [selectedCompetition, fetchFeedbackData]);

  const handleCompetitionChange = useCallback((competitionId: string) => {
    setSelectedCompetition(competitionId);
    setSensorData([]);
    setRaceRecord(null);
    setError('');
  }, []);

  return {
    competitions,
    selectedCompetition,
    sensorData,
    raceRecord,
    isLoading,
    error,
    refreshData,
    handleCompetitionChange,
    setSelectedCompetition: handleCompetitionChange,
  };
};