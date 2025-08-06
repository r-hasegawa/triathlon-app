import { useState, useEffect } from 'react';

export interface ExportHistoryItem {
  id: string;
  filename: string;
  format: string;
  recordCount: number;
  fileSize: number;
  exportedAt: string;
  filters: any;
}

export const useExportHistory = () => {
  const [history, setHistory] = useState<ExportHistoryItem[]>([]);

  useEffect(() => {
    // ローカルストレージからエクスポート履歴を読み込み
    const savedHistory = localStorage.getItem('export_history');
    if (savedHistory) {
      try {
        setHistory(JSON.parse(savedHistory));
      } catch (error) {
        console.error('Failed to load export history:', error);
      }
    }
  }, []);

  const addExportRecord = (record: Omit<ExportHistoryItem, 'id' | 'exportedAt'>) => {
    const newRecord: ExportHistoryItem = {
      ...record,
      id: Date.now().toString(),
      exportedAt: new Date().toISOString(),
    };

    const updatedHistory = [newRecord, ...history].slice(0, 50); // 最新50件のみ保存
    setHistory(updatedHistory);
    localStorage.setItem('export_history', JSON.stringify(updatedHistory));
  };

  const clearHistory = () => {
    setHistory([]);
    localStorage.removeItem('export_history');
  };

  return {
    history,
    addExportRecord,
    clearHistory,
  };
};