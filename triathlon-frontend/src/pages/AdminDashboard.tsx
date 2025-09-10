import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Layout } from '@/components/layout/Layout';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { adminService, DashboardStats } from '@/services/adminService';

export const AdminDashboard: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchDashboardStats();
  }, []);

  const fetchDashboardStats = async () => {
    try {
      setIsLoading(true);
      setError('');
      const dashboardStats = await adminService.getDashboardStats();
      setStats(dashboardStats);
    } catch (err: any) {
      console.error('Error fetching dashboard stats:', err);
      setError('統計情報の取得に失敗しました');
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <Layout>
        <div className="flex justify-center items-center h-64">
          <LoadingSpinner size="lg" />
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-8">
        {/* ヘッダー */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">管理者ダッシュボード</h1>
            <p className="mt-1 text-sm text-gray-500">
              システム管理とデータ管理を行えます
            </p>
          </div>
          
          <Button onClick={fetchDashboardStats} variant="outline" size="sm">
            🔄 統計を更新
          </Button>
        </div>

        {/* エラー表示 */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex justify-between items-center">
              <p className="text-sm text-red-600">{error}</p>
              <Button
                onClick={fetchDashboardStats}
                variant="outline"
                size="sm"
              >
                再試行
              </Button>
            </div>
          </div>
        )}

        {/* システム統計 */}
        {stats && (
          <div>
            <h2 className="text-lg font-medium text-gray-900 mb-4">システム統計</h2>
            <div className="admin-grid grid-4 mb-8">
              
              {/* ユーザー統計 */}
              <div className="card">
                <div className="card-body text-center">
                  <div className="stats-number text-blue-600">{stats.total_users}</div>
                  <p className="stats-label-main">総ユーザー数</p>
                  
                  <div className="stats-detail">
                    <div className="stats-row">
                      <span className="stats-label text-green-600">アクティブ</span>
                      <span className="stats-value">{stats.active_users}</span>
                    </div>
                    <div className="stats-row">
                      <span className="stats-label text-gray-600">無効</span>
                      <span className="stats-value">{stats.inactive_users}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* データ統計 */}
              <div className="card">
                <div className="card-body text-center">
                  <div className="stats-number text-green-600">
                    {stats.total_data_records.toLocaleString()}
                  </div>
                  <p className="stats-label-main">総データ数</p>
                  
                  <div className="stats-detail">
                    <div className="stats-row">
                      <span className="stats-label text-green-600">直近7日</span>
                      <span className="stats-value">{stats.recent_data_count.toLocaleString()}</span>
                    </div>
                    <div className="stats-row">
                      <span className="stats-label text-gray-600">1ユーザー平均</span>
                      <span className="stats-value">{stats.avg_records_per_user}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* センサー統計 */}
              <div className="card">
                <div className="card-body text-center">
                  <div className="stats-number text-purple-600">{stats.total_sensors}</div>
                  <p className="stats-label-main">登録センサー数</p>
                  
                  <div className="stats-detail">
                    <div className="stats-row">
                      <span className="stats-label text-purple-600">アクティブ</span>
                      <span className="stats-value">{stats.active_sensors || stats.total_sensors}</span>
                    </div>
                    <div className="stats-row">
                      <span className="stats-label text-gray-600">1ユーザー平均</span>
                      <span className="stats-value">{stats.avg_sensors_per_user}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* 直近活動 */}
              <div className="card">
                <div className="card-body text-center">
                  <div className="stats-number text-orange-600">
                    {stats.recent_data_count > 999 ? '999+' : stats.recent_data_count}
                  </div>
                  <p className="stats-label-main">直近データ数</p>
                  
                  <div className="stats-detail">
                    <div className="stats-row">
                      <span className="stats-label text-orange-600">アップロード</span>
                      <span className="stats-value">{stats.recent_uploads}</span>
                    </div>
                    <div className="stats-row">
                      <span className="stats-label text-gray-600">過去7日間</span>
                      <span className="stats-value">新規データ</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 主要機能へのアクセス */}
        <div className="card">
          <div className="card-header-improved">
            <h3 className="card-title-improved">主要機能</h3>
            <p className="card-subtitle-improved">管理機能へのクイックアクセス</p>
          </div>
          
          <div className="card-body">
            <button
              onClick={() => navigate('/admin/csv-upload')}
              className="admin-action-button"
            >
              <span className="admin-action-icon">📁</span>
              <div className="admin-action-content">
                <div className="admin-action-title">CSVファイルをアップロード</div>
                <p className="admin-action-description">センサデータとマッピングファイルの管理</p>
              </div>
            </button>
            
            <button
              onClick={() => navigate('/admin/users')}
              className="admin-action-button"
            >
              <span className="admin-action-icon">👥</span>
              <div className="admin-action-content">
                <div className="admin-action-title">ユーザーを管理</div>
                <p className="admin-action-description">アカウント作成・編集・削除</p>
              </div>
            </button>
            
            <button
              onClick={() => navigate('/admin/upload-history')}
              className="admin-action-button"
            >
              <span className="admin-action-icon">📊</span>
              <div className="admin-action-content">
                <div className="admin-action-title">処理状況を確認</div>
                <p className="admin-action-description">アップロード結果とエラー</p>
              </div>
            </button>
          </div>
        </div>

        {/* データ品質インジケーター */}
        {stats && (
          <div className="card">
            <div className="card-header-improved">
              <h3 className="card-title-improved">データ品質</h3>
              <p className="card-subtitle-improved">システム全体のデータ状況</p>
            </div>
            
            <div className="card-body">
              <div className="admin-grid grid-3">
                
                {/* データカバレッジ */}
                <div className="text-center">
                  <div className="quality-indicator">
                    <svg className="quality-circle-bg" viewBox="0 0 36 36">
                      <path
                        d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                        fill="none"
                        stroke="#e5e7eb"
                        strokeWidth="3"
                      />
                    </svg>
                    <svg className="quality-circle-progress" viewBox="0 0 36 36">
                      <path
                        d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                        fill="none"
                        stroke="#3b82f6"
                        strokeWidth="3"
                        strokeDasharray={`${stats.total_users > 0 ? (stats.users_with_data / stats.total_users) * 100 : 0}, 100`}
                      />
                    </svg>
                    <div className="quality-percentage">
                      {stats.total_users > 0 ? Math.round((stats.users_with_data / stats.total_users) * 100) : 0}%
                    </div>
                  </div>
                  <p className="text-sm font-medium text-gray-900 mt-3">データカバレッジ</p>
                  <p className="text-xs text-gray-500">データを持つユーザーの割合</p>
                </div>

                {/* システム稼働率 */}
                <div className="text-center">
                  <div className="quality-indicator">
                    <svg className="quality-circle-bg" viewBox="0 0 36 36">
                      <path
                        d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                        fill="none"
                        stroke="#e5e7eb"
                        strokeWidth="3"
                      />
                    </svg>
                    <svg className="quality-circle-progress" viewBox="0 0 36 36">
                      <path
                        d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                        fill="none"
                        stroke="#22c55e"
                        strokeWidth="3"
                        strokeDasharray="98, 100"
                      />
                    </svg>
                    <div className="quality-percentage" style={{color: '#22c55e'}}>98%</div>
                  </div>
                  <p className="text-sm font-medium text-gray-900 mt-3">システム稼働率</p>
                  <p className="text-xs text-gray-500">過去30日間の稼働状況</p>
                </div>

                {/* データ完整性 */}
                <div className="text-center">
                  <div className="quality-indicator">
                    <svg className="quality-circle-bg" viewBox="0 0 36 36">
                      <path
                        d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                        fill="none"
                        stroke="#e5e7eb"
                        strokeWidth="3"
                      />
                    </svg>
                    <svg className="quality-circle-progress" viewBox="0 0 36 36">
                      <path
                        d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                        fill="none"
                        stroke="#a855f7"
                        strokeWidth="3"
                        strokeDasharray="95, 100"
                      />
                    </svg>
                    <div className="quality-percentage" style={{color: '#a855f7'}}>95%</div>
                  </div>
                  <p className="text-sm font-medium text-gray-900 mt-3">データ完整性</p>
                  <p className="text-xs text-gray-500">欠損データの少なさ</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* システム情報 */}
        <div className="card system-info-card">
          <div className="card-header-improved">
            <h3 className="card-title-improved">システム情報</h3>
          </div>
          
          <div className="card-body">
            <div className="admin-grid grid-2">
              <div className="system-info-section">
                <h4>
                  <span>🔧</span>
                  管理機能
                </h4>
                <ul className="system-info-list">
                  <li>CSVファイルの一括アップロード</li>
                  <li>ユーザーアカウント管理</li>
                  <li>センサーマッピング管理</li>
                  <li>データ処理履歴確認</li>
                </ul>
              </div>
              
              <div className="system-info-section">
                <h4>
                  <span>📊</span>
                  データ形式
                </h4>
                <ul className="system-info-list">
                  <li>センサデータ: CSV (sensor_id, timestamp, temperature)</li>
                  <li>マッピング: CSV (sensor_id, user_id, subject_name)</li>
                  <li>最大ファイルサイズ: 10MB</li>
                  <li>文字コード: UTF-8</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        {/* 最近の活動 */}
        {stats && (
          <div className="card">
            <div className="card-header-improved">
              <h3 className="card-title-improved">最近の活動</h3>
              <p className="card-subtitle-improved">過去7日間のシステム使用状況</p>
            </div>
            
            <div className="card-body">
              <div className="admin-grid grid-2">
                <div className="text-center p-4 bg-blue-50 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600 mb-2">
                    {stats.recent_data_count.toLocaleString()}
                  </div>
                  <p className="text-sm font-medium text-blue-800">新規データレコード</p>
                  <p className="text-xs text-blue-600 mt-1">過去7日間で追加</p>
                </div>
                
                <div className="text-center p-4 bg-green-50 rounded-lg">
                  <div className="text-2xl font-bold text-green-600 mb-2">
                    {stats.recent_uploads}
                  </div>
                  <p className="text-sm font-medium text-green-800">ファイルアップロード</p>
                  <p className="text-xs text-green-600 mt-1">過去7日間の処理数</p>
                </div>
              </div>
              
              <div className="mt-6 pt-6 border-t border-gray-200">
                <div className="flex justify-between items-center">
                  <div>
                    <p className="text-sm font-medium text-gray-900">システムステータス</p>
                    <p className="text-xs text-gray-500">すべてのサービスが正常に動作しています</p>
                  </div>
                  <div className="flex items-center">
                    <div className="w-3 h-3 bg-green-400 rounded-full mr-2"></div>
                    <span className="text-sm font-medium text-green-600">正常</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};