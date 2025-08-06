import React from 'react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';

export interface UserFilters {
  search: string;
  status: 'all' | 'active' | 'inactive';
  hasData: 'all' | 'with-data' | 'no-data';
}

interface UserFiltersProps {
  filters: UserFilters;
  onFiltersChange: (filters: UserFilters) => void;
  onReset: () => void;
  userCount: number;
}

export const UserFiltersComponent: React.FC<UserFiltersProps> = ({
  filters,
  onFiltersChange,
  onReset,
  userCount,
}) => {
  const updateFilter = (key: keyof UserFilters, value: string) => {
    onFiltersChange({
      ...filters,
      [key]: value,
    });
  };

  return (
    <div className="bg-white p-4 rounded-lg shadow space-y-4">
      <div className="flex flex-wrap gap-4 items-end">
        <div className="flex-1 min-w-64">
          <Input
            label="検索"
            type="text"
            placeholder="ユーザーID、ユーザー名、フルネームで検索..."
            value={filters.search}
            onChange={(e) => updateFilter('search', e.target.value)}
          />
        </div>

        <div className="min-w-32">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            ステータス
          </label>
          <select
            value={filters.status}
            onChange={(e) => updateFilter('status', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">すべて</option>
            <option value="active">アクティブ</option>
            <option value="inactive">無効</option>
          </select>
        </div>

        <div className="min-w-32">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            データ有無
          </label>
          <select
            value={filters.hasData}
            onChange={(e) => updateFilter('hasData', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">すべて</option>
            <option value="with-data">データあり</option>
            <option value="no-data">データなし</option>
          </select>
        </div>

        <Button
          variant="outline"
          onClick={onReset}
        >
          リセット
        </Button>
      </div>

      <div className="text-sm text-gray-600">
        {userCount > 0 ? (
          <>検索結果: {userCount}名のユーザー</>
        ) : (
          <>該当するユーザーが見つかりません</>
        )}
      </div>
    </div>
  );
};