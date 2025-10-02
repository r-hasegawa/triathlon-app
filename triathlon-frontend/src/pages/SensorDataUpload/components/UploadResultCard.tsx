// triathlon-frontend/src/pages/SensorDataUpload/components/UploadResultCard.tsx

import React from 'react';
import { UploadResult, SensorDetail, RaceRecordsUploadResult } from '../index';

interface UploadResultCardProps {
  results: UploadResult[] | RaceRecordsUploadResult | null;
  type: 'multiple' | 'single' | 'race-records';
}

const UploadResultCard: React.FC<UploadResultCardProps> = ({ results, type }) => {
  if (!results) return null;

  // 大会記録の場合
  if (type === 'race-records') {
    const result = results as RaceRecordsUploadResult;
    return (
      <div className={`p-4 border rounded mt-4 ${result.success ? 'bg-green-50 border-green-300' : 'bg-red-50 border-red-300'}`}>
        <div className="font-semibold mb-2">{result.message}</div>
        {result.success && (
          <div className="space-y-1 text-sm">
            <div>📊 参加者数: {result.participants_count}名</div>
            <div>📝 総記録数: {result.total_records}件</div>
            <div>🗑️ 削除された旧記録: {result.deleted_old_records}件</div>
            <div>📁 処理ファイル数: {result.total_files}個</div>
            <div className="text-gray-600">⏰ {new Date(result.upload_time).toLocaleString('ja-JP')}</div>
          </div>
        )}
        {result.errors && result.errors.length > 0 && (
          <div className="mt-2">
            <div className="text-red-600 font-medium">エラー詳細:</div>
            <ul className="list-disc list-inside text-sm text-red-600">
              {result.errors.map((err, idx) => <li key={idx}>{err}</li>)}
            </ul>
          </div>
        )}
      </div>
    );
  }

  // 単一ファイルの場合
  if (type === 'single') {
    const result = results as UploadResult;
    const statusClass = result.status === 'success' || result.status === 'SUCCESS'
      ? 'bg-green-50 border-green-300'
      : result.status === 'partial' || result.status === 'PARTIAL'
      ? 'bg-yellow-50 border-yellow-300'
      : 'bg-red-50 border-red-300';

      // 成功数と失敗数を計算するロジックを定義
      let successCount = 0;
      let failedCount = 0;

      // WBGTデータの場合
      if (result.failed_records !== undefined) {
        successCount = (result.processed_records || 0) - (result.failed_records || 0);
        failedCount = result.failed_records || 0;
      } 
      // マッピングデータの場合（skipped_recordsで判定）
      else if (result.skipped_records !== undefined) {
        successCount = (result.processed_records || 0) - (result.skipped_records || 0);
        failedCount = result.skipped_records || 0;
      }
      // その他の場合（フォールバック）
      else {
        successCount = result.success || 0;
        failedCount = result.failed || 0;
      }

    return (
    <div className={`p-4 rounded border mt-4 ${statusClass}`}>
      <div className="font-medium mb-2">📄 {result.file || result.file_name}</div>
      {result.error ? (
        <div className="text-red-600">{result.error}</div>
      ) : (
        <div className="text-sm space-y-1">
          {/* 計算した成功数と失敗数を表示 */}
          {(successCount !== undefined) && (
            <div>✅ 成功: {successCount}件</div>
          )}
          
          {(failedCount || 0) > 0 && (
            <div className="text-red-600">❌ 失敗: {failedCount}件</div>
          )}

          {result.total_records !== undefined && (
            <div>📝 総記録行数: {result.total_records}件</div>
          )}

          {result.message && (
            <div className="text-blue-600">{result.message}</div>
          )}
        </div>
      )}
    </div>
  );
}

  // 複数ファイルの場合
  const multipleResults = results as UploadResult[];
  if (multipleResults.length === 0) return null;

  return (
    <div className="space-y-4 mt-4">
      <h3 className="font-semibold text-lg">アップロード結果</h3>
      {multipleResults.map((result, idx) => {
        const fileName = result.file_name || result.file || `ファイル ${idx + 1}`;
        const statusClass = result.status === 'success' || result.status === 'SUCCESS'
          ? 'bg-green-50 border-green-300'
          : result.status === 'partial' || result.status === 'PARTIAL'
          ? 'bg-yellow-50 border-yellow-300'
          : 'bg-red-50 border-red-300';

        return (
          <div key={idx} className={`p-4 border rounded ${statusClass}`}>
            <div className="font-medium mb-2">📄 {fileName}</div>
            {result.error ? (
              <div className="text-red-600">{result.error}</div>
            ) : (
              <div className="space-y-2 text-sm">
                {/* 基本情報 */}
                {(result.success !== undefined || result.total_success !== undefined) && (
                  <div>
                    ✅ 成功: {result.success || result.total_success || 0}件
                    {(result.failed || result.total_failed || 0) > 0 && (
                      <span className="text-red-600 ml-2">
                        / ❌ 失敗: {result.failed || result.total_failed}件
                      </span>
                    )}
                  </div>
                )}

                {/* センサーID情報 */}
                {result.sensor_ids && result.sensor_ids.length > 0 && (
                  <div>🔍 検出センサーID: {result.sensor_ids.join(', ')}</div>
                )}

                {/* センサー詳細情報（カプセル温用） */}
                {result.sensor_details && result.sensor_details.length > 0 && (
                  <div className="space-y-1">
                    <div className="font-medium">センサー別詳細:</div>
                    {result.sensor_details.map((detail: SensorDetail, detailIdx: number) => (
                      <div key={detailIdx} className="pl-4 border-l-2 border-blue-300">
                        <div>🔹 センサー{detail.sensor_number}: {detail.sensor_id}</div>
                        <div>✅ 成功: {detail.success_count}件 / ❌ 失敗: {detail.failed_count}件</div>
                      </div>
                    ))}
                  </div>
                )}

                {/* 心拍データ用情報 */}
                {result.trackpoints_total !== undefined && (
                  <div>📈 トラックポイント: {result.trackpoints_total}件</div>
                )}
                {result.sensors_found !== undefined && (
                  <div>🔍 検出センサー数: {result.sensors_found}個</div>
                )}

                {/* メッセージ */}
                {result.message && (
                  <div className="text-blue-600">{result.message}</div>
                )}

                {/* エラー詳細 */}
                {result.errors && result.errors.length > 0 && (
                  <div className="mt-2">
                    <div className="text-red-600 font-medium">エラー詳細:</div>
                    <ul className="list-disc list-inside text-sm text-red-600">
                      {result.errors.slice(0, 5).map((err, errIdx) => (
                        <li key={errIdx}>{err}</li>
                      ))}
                      {result.errors.length > 5 && (
                        <li className="text-gray-600">...他 {result.errors.length - 5}件</li>
                      )}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

export default UploadResultCard;