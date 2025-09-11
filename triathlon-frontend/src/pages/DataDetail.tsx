import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Layout } from '@/components/layout/Layout';
import { Card } from '@/components/ui/Card';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { Button } from '@/components/ui/Button';
import { adminService } from '@/services/adminService';
import { dataService } from '@/services/dataService';

export const DataDetail: React.FC = () => {
  const { user } = useAuth();
  const [searchParams] = useSearchParams();
  const [sensorData, setSensorData] = useState<SensorDataItem[]>([]);
  const [sensors, setSensors] = useState<SensorInfo[]>([]);
  const [selectedSensor, setSelectedSensor] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [currentPage, setCurrentPage] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [totalRecords, setTotalRecords] = useState(0);
  const [targetUser, setTargetUser] = useState<UserInfo | null>(null);

  // 管理者モードかどうかを判定
  const isAdmin = user && 'admin_id' in user;
  const targetUserId = searchParams.get('user_id');
  const isAdminMode = isAdmin && targetUserId;

  useEffect(() => {
    console.log('DataDetail mounted - isAdminMode:', isAdminMode, 'targetUserId:', targetUserId);
    fetchInitialData();
  }, [isAdminMode, targetUserId]);

  useEffect(() => {
    if (sensors.length > 0 || !isAdminMode) {
      fetchSensorData();
    }
  }, [selectedSensor, currentPage, sensors]);

  const fetchInitialData = async () => {
    try {
      setIsLoading(true);
      setError('');

      if (isAdminMode && targetUserId) {
        console.log('Fetching admin mode data for user:', targetUserId);
        
        // ユーザー情報を取得
        try {
          const users = await adminService.getUsersWithStats();
          const userInfo = users.find((u: any) => u.user_id === targetUserId);
          if (userInfo) {
            setTargetUser({
              user_id: userInfo.user_id,
              username: userInfo.username,
              full_name: userInfo.full_name
            });
          }
        } catch (error) {
          console.error('Error fetching user info:', error);
        }

        // 管理者として特定ユーザーのセンサーを取得
        try {
          const response = await adminService.getUserSensors(targetUserId);
          console.log('Admin sensors response:', response);
          setSensors(response.sensors || []);
          
          if (response.sensors && response.sensors.length > 0 && !selectedSensor) {
            setSelectedSensor(response.sensors[0].sensor_id);
          }
        } catch (error) {
          console.error('Error fetching user sensors:', error);
          setError('センサー情報の取得に失敗しました');
        }
      } else {
        console.log('Fetching normal user data');
        // 通常ユーザーモード
        try {
          const sensorsData = await dataService.getMySensors();
          console.log('User sensors:', sensorsData);
          setSensors(sensorsData);
          
          if (sensorsData.length > 0 && !selectedSensor) {
            setSelectedSensor(sensorsData[0].sensor_id);
          }
        } catch (error) {
          console.error('Error fetching my sensors:', error);
          setError('センサー情報の取得に失敗しました');
        }
      }
    } catch (error) {
      console.error('Error in fetchInitialData:', error);
      setError('初期データの取得に失敗しました');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchSensorData = async () => {
    try {
      setIsLoading(true);
      setError('');
      
      let data;
      if (isAdminMode && targetUserId) {
        console.log('Fetching admin sensor data for user:', targetUserId, 'sensor:', selectedSensor);
        // 管理者として特定ユーザーのデータを取得
        data = await adminService.getUserData(targetUserId, {
          sensorId: selectedSensor || undefined,
          page: currentPage,
          limit: 100,
          order: 'desc'
        });
        console.log('Admin data response:', data);
      } else {
        console.log('Fetching user sensor data');
        // 自分のデータを取得
        data = await dataService.getMyData({
          sensor_id: selectedSensor || undefined,
          page: currentPage,
          limit: 100,
          order: 'desc'
        });
        console.log('User data response:', data);
      }
      
      setSensorData(data.data || []);
      setTotalRecords(data.total || 0);
      setTotalPages(Math.ceil((data.total || 0) / 100));
    } catch (error: any) {
      console.error('Error fetching sensor data:', error);
      setError('データの取得に失敗しました: ' + (error.message || 'Unknown error'));
    } finally {
      setIsLoading(false);
    }
  };

  const handleExport = async (format: 'csv' | 'json') => {
    try {
      let blob;
      let filename;
      
      if (isAdminMode && targetUserId) {
        // 管理者として特定ユーザーのデータをエクスポート
        const response = await fetch(
          `http://localhost:8000/admin/users/${targetUserId}/data/export?format=${format}${selectedSensor ? `&sensor_id=${selectedSensor}` : ''}`,
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
          }
        );
        
        if (!response.ok) {
          throw new Error('Export failed');
        }
        
        blob = await response.blob();
        filename = `sensor_data_${targetUserId}_${new Date().toISOString()}.${format}`;
      } else {
        // 自分のデータをエクスポート
        blob = await dataService.exportData(format, {
          sensor_id: selectedSensor || undefined
        });
        filename = `sensor_data_${new Date().toISOString()}.${format}`;
      }
      
      // ダウンロード処理
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      
      alert(`データを${format.toUpperCase()}形式でエクスポートしました`);
    } catch (error) {
      console.error('Export error:', error);
      alert('データのエクスポートに失敗しました');
    }
  };

  const handleRefresh = () => {
    fetchSensorData();
  };

  return (
    <Layout>
      <div className="space-y-6">
        {/* ヘッダー */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            {isAdminMode ? 'ユーザーデータ詳細（管理者モード）' : 'センサーデータ詳細'}
          </h1>
          {isAdminMode && targetUser && (
            <p className="mt-2 text-sm text-gray-600">
              表示中のユーザー: {targetUser.full_name} ({targetUser.username}) - ID: {targetUser.user_id}
            </p>
          )}
        </div>

        {/* エラー表示 */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex justify-between items-center">
              <p className="text-sm text-red-600">{error}</p>
              <Button
                onClick={fetchInitialData}
                variant="outline"
                size="sm"
              >
                再試行
              </Button>
            </div>
          </div>
        )}

        {/* センサー選択とアクション */}
        <Card title="データコントロール">
          <div className="space-y-4">
            <div>
              <label htmlFor="sensor-select" className="block text-sm font-medium text-gray-700 mb-2">
                センサー選択
              </label>
              <select
                id="sensor-select"
                value={selectedSensor}
                onChange={(e) => {
                  setSelectedSensor(e.target.value);
                  setCurrentPage(0);
                }}
                className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                disabled={isLoading}
              >
                <option value="">全てのセンサー</option>
                {sensors.map((sensor) => (
                  <option key={sensor.sensor_id} value={sensor.sensor_id}>
                    {sensor.sensor_id} - {sensor.device_type || 'Unknown Device'}
                    {sensor.subject_name && ` (${sensor.subject_name})`}
                  </option>
                ))}
              </select>
            </div>
            
            <div className="flex justify-between items-center">
              <p className="text-sm text-gray-600">
                {totalRecords > 0 
                  ? `全${totalRecords}件中 ${currentPage * 100 + 1}〜${Math.min((currentPage + 1) * 100, totalRecords)}件を表示`
                  : 'データがありません'}
              </p>
              
              <div className="flex space-x-2">
                <Button
                  onClick={handleRefresh}
                  variant="outline"
                  size="sm"
                  disabled={isLoading}
                >
                  🔄 更新
                </Button>
                <Button
                  onClick={() => handleExport('csv')}
                  variant="outline"
                  size="sm"
                  disabled={isLoading || sensorData.length === 0}
                >
                  📥 CSV
                </Button>
                <Button
                  onClick={() => handleExport('json')}
                  variant="outline"
                  size="sm"
                  disabled={isLoading || sensorData.length === 0}
                >
                  📥 JSON
                </Button>
              </div>
            </div>
          </div>
        </Card>

        {/* データテーブル */}
        <Card title="センサーデータ">
          {isLoading ? (
            <div className="flex justify-center py-12">
              <LoadingSpinner size="lg" text="データを読み込み中..." />
            </div>
          ) : sensorData.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <p>表示するデータがありません</p>
              {sensors.length === 0 && (
                <p className="text-sm mt-2">センサーが登録されていません</p>
              )}
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        タイムスタンプ
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        センサーID
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        温度 (°C)
                      </th>
                      {isAdminMode && (
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          ユーザーID
                        </th>
                      )}
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {sensorData.map((data, index) => (
                      <tr key={index} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {new Date(data.timestamp).toLocaleString('ja-JP')}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {data.sensor_id}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {typeof data.temperature === 'number' 
                            ? data.temperature.toFixed(2) 
                            : 'N/A'}
                        </td>
                        {isAdminMode && (
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {data.user_id || targetUserId}
                          </td>
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              
              {/* ページネーション */}
              {totalPages > 1 && (
                <div className="mt-4 flex justify-center items-center space-x-2">
                  <Button
                    onClick={() => setCurrentPage(Math.max(0, currentPage - 1))}
                    disabled={currentPage === 0 || isLoading}
                    variant="outline"
                    size="sm"
                  >
                    前へ
                  </Button>
                  
                  <span className="px-4 py-2 text-sm text-gray-700">
                    ページ {currentPage + 1} / {totalPages}
                  </span>
                  
                  <Button
                    onClick={() => setCurrentPage(Math.min(totalPages - 1, currentPage + 1))}
                    disabled={currentPage >= totalPages - 1 || isLoading}
                    variant="outline"
                    size="sm"
                  >
                    次へ
                  </Button>
                </div>
              )}
            </>
          )}
        </Card>
      </div>
    </Layout>
  );
};