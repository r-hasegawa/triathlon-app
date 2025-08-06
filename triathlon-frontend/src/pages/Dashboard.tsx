import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Layout } from '@/components/layout/Layout';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { TemperatureChart } from '@/components/charts/TemperatureChart';
import { StatisticsCard } from '@/components/charts/StatisticsCard';
import { useSensorData } from '@/hooks/useSensorData';

export const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { sensors, stats, isLoading, error, refetch } = useSensorData();

  const isAdmin = user && 'admin_id' in user;

  if (isLoading) {
    return (
      <Layout>
        <div className="flex justify-center items-center h-64">
          <LoadingSpinner size="lg" />
        </div>
      </Layout>
    );
  }

  // 管理者ダッシュボード
  if (isAdmin) {
    return (
      <Layout>
        <div className="space-y-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">管理者ダッシュボード</h1>
            <p className="mt-1 text-sm text-gray-500">
              システム管理とデータ管理を行えます
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <Card 
              title="CSVアップロード" 
              className="cursor-pointer hover:shadow-xl transition-shadow"
              onClick={() => navigate('/admin/csv-upload')}
            >
              <div className="space-y-4">
                <p className="text-gray-600">センサデータとマッピングファイルをアップロード</p>
                <Button variant="primary" size="sm" className="w-full">
                  📤 アップロード画面へ
                </Button>
              </div>
            </Card>
            
            <Card 
              title="ユーザー管理" 
              className="cursor-pointer hover:shadow-xl transition-shadow"
              onClick={() => navigate('/admin/users')}
            >
              <div className="space-y-4">
                <p className="text-gray-600">被験者アカウントの作成・管理</p>
                <Button variant="primary" size="sm" className="w-full">
                  👥 ユーザー管理画面へ
                </Button>
              </div>
            </Card>
            
            <Card 
              title="アップロード履歴" 
              className="cursor-pointer hover:shadow-xl transition-shadow"
              onClick={() => navigate('/admin/upload-history')}
            >
              <div className="space-y-4">
                <p className="text-gray-600">過去のデータアップロード履歴を確認</p>
                <Button variant="primary" size="sm" className="w-full">
                  📋 履歴を表示
                </Button>
              </div>
            </Card>
          </div>

          {/* クイックアクション */}
          <Card title="クイックアクション">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Button
                variant="outline"
                onClick={() => navigate('/admin/csv-upload')}
                className="justify-start"
              >
                <span className="mr-2">⚡</span>
                新しいデータをアップロード
              </Button>
              
              <Button
                variant="outline"
                onClick={() => navigate('/admin/users')}
                className="justify-start"
              >
                <span className="mr-2">👥</span>
                ユーザーを管理
              </Button>
              
              <Button
                variant="outline"
                onClick={() => navigate('/admin/upload-history')}
                className="justify-start"
              >
                <span className="mr-2">📊</span>
                最新の処理状況を確認
              </Button>
            </div>
          </Card>

          {/* システム統計 */}
          <Card title="システム統計" subtitle="全体のデータ統計情報">
            <div className="text-center py-8 text-gray-500">
              <p>システム全体の統計情報</p>
              <p className="text-sm mt-1">
                詳細な統計は各管理画面でご確認いただけます
              </p>
            </div>
          </Card>
        </div>
      </Layout>
    );
  }

  // 被験者ダッシュボード
  return (
    <Layout>
      <div className="space-y-8">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              ようこそ、{user?.full_name || user?.username}さん
            </h1>
            <p className="mt-1 text-sm text-gray-500">
              あなたのセンサデータを確認できます
            </p>
          </div>
          
          <Button
            onClick={refetch}
            variant="outline"
            size="sm"
          >
            データを更新
          </Button>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex justify-between items-center">
              <p className="text-sm text-red-600">{error}</p>
              <Button
                onClick={refetch}
                variant="outline"
                size="sm"
              >
                再試行
              </Button>
            </div>
          </div>
        )}

        {/* 統計情報カード */}
        {stats && (
          <div>
            <h2 className="text-lg font-medium text-gray-900 mb-4">データ統計</h2>
            <StatisticsCard stats={stats} isLoading={isLoading} />
          </div>
        )}

        {/* 温度グラフ */}
        <div>
          <h2 className="text-lg font-medium text-gray-900 mb-4">体表温度の推移</h2>
          <TemperatureChart sensors={sensors} height={450} />
        </div>

        {/* クイックアクション */}
        <Card title="データ分析">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Button
              variant="outline"
              onClick={() => navigate('/data-detail')}
              className="justify-start"
            >
              <span className="mr-2">📋</span>
              詳細データを表示
            </Button>
            
            <Button
              variant="outline"
              onClick={() => {
                // データエクスポート機能（データ詳細画面でも利用可能）
                navigate('/data-detail');
              }}
              className="justify-start"
            >
              <span className="mr-2">📥</span>
              データをエクスポート
            </Button>
            
            <Button
              variant="outline"
              onClick={refetch}
              className="justify-start"
            >
              <span className="mr-2">🔄</span>
              データを再読み込み
            </Button>
          </div>
        </Card>

        {/* センサー一覧 */}
        <Card title="登録済みセンサー" subtitle={`${sensors.length}個のセンサーが登録されています`}>
          {sensors.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <p>登録されているセンサーがありません</p>
              <p className="text-sm mt-1">管理者にお問い合わせください</p>
            </div>
          ) : (
            <div className="space-y-3">
              {sensors.map((sensor) => (
                <div key={sensor.id} className="flex justify-between items-center p-4 bg-gray-50 rounded-lg border border-gray-200">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3">
                      <p className="font-medium text-gray-900">{sensor.sensor_id}</p>
                      <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                        sensor.is_active 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {sensor.is_active ? 'アクティブ' : '非アクティブ'}
                      </span>
                    </div>
                    <p className="text-sm text-gray-500 mt-1">
                      {sensor.subject_name || 'センサー名未設定'} • {sensor.device_type}
                    </p>
                    <p className="text-xs text-gray-400 mt-1">
                      登録日: {new Date(sensor.created_at).toLocaleDateString('ja-JP')}
                    </p>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => navigate(`/data-detail?sensor_id=${sensor.sensor_id}`)}
                    >
                      詳細データ
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* データ期間情報 */}
        {stats && stats.start_time && stats.end_time && (
          <Card title="データ収集期間">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-blue-50 p-4 rounded-lg">
                <p className="text-sm font-medium text-blue-900 mb-1">データ開始</p>
                <p className="text-lg font-semibold text-blue-800">
                  {new Date(stats.start_time).toLocaleDateString('ja-JP', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                  })}
                </p>
              </div>
              <div className="bg-green-50 p-4 rounded-lg">
                <p className="text-sm font-medium text-green-900 mb-1">最終更新</p>
                <p className="text-lg font-semibold text-green-800">
                  {new Date(stats.end_time).toLocaleDateString('ja-JP', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                  })}
                </p>
              </div>
            </div>
            
            {/* データ収集期間の計算 */}
            <div className="mt-4 text-center">
              <p className="text-sm text-gray-600">
                データ収集期間: {Math.ceil((new Date(stats.end_time).getTime() - new Date(stats.start_time).getTime()) / (1000 * 60 * 60 * 24))}日間
              </p>
            </div>
          </Card>
        )}
      </div>
    </Layout>
  );
};