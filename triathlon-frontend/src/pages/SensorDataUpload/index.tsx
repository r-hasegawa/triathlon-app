// triathlon-frontend/src/pages/SensorDataUpload/index.tsx

import React, { useState, useEffect } from 'react';
import { Layout } from '@/components/layout/Layout';
import { Card } from '@/components/ui/Card';
import CompetitionSelector from './components/CompetitionSelector';
import SkinTemperatureUpload from './components/SkinTemperatureUpload';
import CoreTemperatureUpload from './components/CoreTemperatureUpload';
import HeartRateUpload from './components/HeartRateUpload';
import WbgtUpload from './components/WbgtUpload';
import MappingUpload from './components/MappingUpload';
import RaceRecordUpload from './components/RaceRecordUpload';
import UploadHistoryTable from './components/UploadHistoryTable';

// ========================================
// 型定義
// ========================================

export interface Competition {
  competition_id: string;
  name: string;
  date: string;
  location: string;
}

export interface SensorDetail {
  sensor_number: number;
  sensor_id: string;
  success_count: number;
  failed_count: number;
  total_count: number;
}

export interface UploadResult {
  file?: string;
  file_name?: string;
  batch_id?: string;
  success?: number;
  failed?: number;
  total?: number;
  total_success?: number;
  total_failed?: number;
  status: string;
  error?: string;
  sensor_ids?: string[];
  sensor_details?: SensorDetail[];
  trackpoints_total?: number;
  sensors_found?: number;
  message?: string;
  processed?: number;
  skipped?: number;
  errors?: string[];
}

export interface RaceRecordsUploadResult {
  success: boolean;
  message: string;
  batch_id: string;
  competition_id: string;
  competition_name: string;
  total_files: number;
  participants_count: number;
  total_records: number;
  deleted_old_records: number;
  errors?: string[];
  upload_time: string;
}

export interface UploadBatch {
  batch_id: string;
  sensor_type: string;
  file_name: string;
  total_records: number;
  success_records: number;
  failed_records: number;
  status: string;
  uploaded_at: string;
  uploaded_by: string;
}

// ========================================
// カスタムフック
// ========================================

export const useCompetitions = () => {
  const [competitions, setCompetitions] = useState<Competition[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const loadCompetitions = async () => {
    setIsLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:8000/admin/competitions', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setCompetitions(Array.isArray(data) ? data : data.competitions || []);
      }
    } catch (error) {
      console.error('大会取得エラー:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadCompetitions();
  }, []);

  return { competitions, isLoading, reload: loadCompetitions };
};

export const useUploadBatches = () => {
  const [batches, setBatches] = useState<UploadBatch[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const loadBatches = async (competitionId?: string) => {
    if (!competitionId) {
      setBatches([]);
      return;
    }

    setIsLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const url = `http://localhost:8000/admin/batches?competition_id=${competitionId}`;
      const response = await fetch(url, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setBatches(data.batches || []);
      }
    } catch (error) {
      console.error('履歴取得エラー:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const deleteBatch = async (batchId: string) => {
    if (!confirm('このバッチとすべてのデータを削除しますか?')) return;

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`http://localhost:8000/admin/batches/${batchId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        alert('バッチを削除しました');
        // 削除後、現在選択中の大会のバッチを再読み込み
        const currentBatches = batches.filter(b => b.batch_id !== batchId);
        setBatches(currentBatches);
      } else {
        alert('削除に失敗しました');
      }
    } catch (error) {
      console.error('削除エラー:', error);
      alert('削除エラーが発生しました');
    }
  };

  return { batches, isLoading, reload: loadBatches, deleteBatch };
};

// export const useFileUpload = (endpoint: string) => {
//   const [isLoading, setIsLoading] = useState(false);

//   const upload = async (
//     files: FileList | File,
//     competitionId: string,
//     additionalData?: Record<string, any>
//   ): Promise<any> => {
//     setIsLoading(true);
//     try {
//       const formData = new FormData();
//       formData.append('competition_id', competitionId);

//       console.log(formData);

//       if (files instanceof FileList) {
//         for (let i = 0; i < files.length; i++) {
//           formData.append('files', files[i]);
//         }
//       } else {
//         formData.append('file', files);
//       }

//       if (additionalData) {
//         Object.entries(additionalData).forEach(([key, value]) => {
//           formData.append(key, value);
//         });
//       }

//       // console.log(additionalData);
//       // console.log(formData);

//       const token = localStorage.getItem('access_token');
//       const response = await fetch(`http://localhost:8000${endpoint}`, {
//         method: 'POST',
//         headers: { 'Authorization': `Bearer ${token}` },
//         body: formData
//       });

//       const result = await response.json();
//       return { success: response.ok, data: result };
//     } catch (error) {
//       console.error('アップロードエラー:', error);
//       return { success: false, error: 'アップロードエラーが発生しました' };
//     } finally {
//       setIsLoading(false);
//     }
//   };

//   return { upload, isLoading };
// };

export const useFileUpload = (endpoint: string) => {
  const [isLoading, setIsLoading] = useState(false);

  const upload = async (
    files: FileList | File,
    competitionId: string,
    fileFieldName: string, 
    additionalData?: Record<string, any>
  ): Promise<any> => {
    setIsLoading(true);

    try {
      const formData = new FormData();
      formData.append('competition_id', competitionId);

      if (files instanceof FileList) {
        for (let i = 0; i < files.length; i++) {
          formData.append(fileFieldName, files[i]);
        }
      } else {
        formData.append(fileFieldName, files);
      }

      if (additionalData) {
        Object.entries(additionalData).forEach(([key, value]) => {
          formData.append(key, value);
        });
      }

      const token = localStorage.getItem('access_token');
      const url = `http://localhost:8000${endpoint}`;
      const headers = { 'Authorization': `Bearer ${token}` };

      const response = await fetch(url, {
        method: 'POST',
        headers,
        body: formData,
      });

      const result = await response.json();

      return { success: response.ok, data: result };
    } catch (error) {
      // [5] エラー発生時のログ
      console.error('--- アップロード処理中にエラーが発生しました ---');
      console.error('エラーの詳細:', error);
      console.error('-----------------------------------------------');
      return { success: false, error: 'アップロードエラーが発生しました' };
    } finally {
      setIsLoading(false);
    }
  };

  return { upload, isLoading };
};

// ========================================
// メインコンポーネント
// ========================================

export const SensorDataUpload: React.FC = () => {
  const [selectedCompetition, setSelectedCompetition] = useState('');
  const { competitions } = useCompetitions();
  const { batches, reload: reloadBatches, deleteBatch } = useUploadBatches();

  // 大会選択時にバッチを読み込む
  const handleCompetitionSelect = (competitionId: string) => {
    setSelectedCompetition(competitionId);
    reloadBatches(competitionId);
  };

  return (
    <Layout>
      <div className="max-w-6xl mx-auto p-6 space-y-6">
        {/* ヘッダー */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900">データアップロード</h1>
          <p className="text-gray-600 mt-2">センサーデータ・大会記録・マッピング情報をアップロード</p>
        </div>

        {/* 大会選択 */}
        <CompetitionSelector
          competitions={competitions}
          selectedCompetition={selectedCompetition}
          onSelect={handleCompetitionSelect}
        />

        {/* アップロードセクション */}
        {selectedCompetition && (
          <>
            <SkinTemperatureUpload 
              competitionId={selectedCompetition}
              onUploadComplete={() => reloadBatches(selectedCompetition)}
            />
            
            <CoreTemperatureUpload 
              competitionId={selectedCompetition}
              onUploadComplete={() => reloadBatches(selectedCompetition)}
            />
            
            <HeartRateUpload 
              competitionId={selectedCompetition}
              onUploadComplete={() => reloadBatches(selectedCompetition)}
            />
            
            <WbgtUpload 
              competitionId={selectedCompetition}
              onUploadComplete={() => reloadBatches(selectedCompetition)}
            />
            
            <MappingUpload 
              competitionId={selectedCompetition}
              onUploadComplete={() => reloadBatches(selectedCompetition)}
            />
            
            <RaceRecordUpload 
              competitionId={selectedCompetition}
              onUploadComplete={() => reloadBatches(selectedCompetition)}
            />

            {/* アップロード履歴 */}
            <UploadHistoryTable 
              batches={batches}
              onDelete={deleteBatch}
              onRefresh={() => reloadBatches(selectedCompetition)}
            />
          </>
        )}
      </div>
    </Layout>
  );
};

export default SensorDataUpload;