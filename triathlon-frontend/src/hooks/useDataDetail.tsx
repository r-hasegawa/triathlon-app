import { useState, useEffect, useCallback } from 'react';
import { dataService } from '@/services/dataService';
import { SensorData, SensorMapping } from '@/types/sensor';
import { FilterOptions } from '@/components/data/DataFilters';

export const useDataDetail = () => {
  const [data, setData] = useState<SensorData[]>([]);
  const [sensors, setSensors] = useState<SensorMapping[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [pageIndex, setPageIndex] = useState(0);
  const [pageSize, setPageSize] = useState(50);
  const [filters, setFilters] = useState<FilterOptions>({});
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  // センサー一覧取得
  useEffect(() => {
    const fetchSensors = async () => {
      try {
        const sensorsData = await dataService.getMySensors();
        setSensors(sensorsData);
      } catch (err: any) {
        console.error('Error fetching sensors:', err);
        setError('センサー情報の取得に失敗しました');
      }
    };
    fetchSensors();
  }, []);

  // データ取得
  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError('');

      const params = {
        ...filters,
        page: pageIndex,
        limit: pageSize,
        order: 'desc' as const,
      };

      const response = await dataService.getMyData(params);
      setData(response.data);
      setTotalCount(response.total);
    } catch (err: any) {
      console.error('Error fetching data:', err);
      setError('データの取得に失敗しました');
      setData([]);
      setTotalCount(0);
    } finally {
      setIsLoading(false);
    }
  }, [filters, pageIndex, pageSize]);

  // フィルターやページが変更された時にデータ取得
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // フィルター変更時はページを最初に戻す
  const handleFiltersChange = (newFilters: FilterOptions) => {
    setFilters(newFilters);
    setPageIndex(0);
  };

  const handlePageChange = (newPageIndex: number) => {
    setPageIndex(newPageIndex);
  };

  const handlePageSizeChange = (newPageSize: number) => {
    setPageSize(newPageSize);
    setPageIndex(0); // ページサイズ変更時は最初のページに戻す
  };

  const handleReset = () => {
    setFilters({});
    setPageIndex(0);
  };

  const refetch = () => {
    fetchData();
  };

  return {
    data,
    sensors,
    totalCount,
    pageIndex,
    pageSize,
    filters,
    isLoading,
    error,
    handleFiltersChange,
    handlePageChange,
    handlePageSizeChange,
    handleReset,
    refetch,
  };
};