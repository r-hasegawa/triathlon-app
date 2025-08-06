import React, { useMemo } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getPaginationRowModel,
  SortingState,
  flexRender,
  createColumnHelper,
} from '@tanstack/react-table';
import { SensorData } from '@/types/sensor';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

interface SensorDataTableProps {
  data: SensorData[];
  isLoading: boolean;
  totalCount: number;
  pageIndex: number;
  pageSize: number;
  onPageChange: (pageIndex: number) => void;
  onPageSizeChange: (pageSize: number) => void;
}

const columnHelper = createColumnHelper<SensorData>();

export const SensorDataTable: React.FC<SensorDataTableProps> = ({
  data,
  isLoading,
  totalCount,
  pageIndex,
  pageSize,
  onPageChange,
  onPageSizeChange,
}) => {
  const [sorting, setSorting] = React.useState<SortingState>([
    { id: 'timestamp', desc: true } // デフォルトで新しい順
  ]);

  const columns = useMemo(
    () => [
      columnHelper.accessor('timestamp', {
        header: '日時',
        cell: (info) => {
          const date = new Date(info.getValue());
          return (
            <div className="text-sm">
              <div className="font-medium text-gray-900">
                {date.toLocaleDateString('ja-JP')}
              </div>
              <div className="text-gray-500">
                {date.toLocaleTimeString('ja-JP')}
              </div>
            </div>
          );
        },
        sortingFn: 'datetime',
      }),
      columnHelper.accessor('sensor_id', {
        header: 'センサーID',
        cell: (info) => (
          <span className="font-mono text-sm bg-gray-100 px-2 py-1 rounded">
            {info.getValue()}
          </span>
        ),
      }),
      columnHelper.accessor('temperature', {
        header: '体表温度',
        cell: (info) => {
          const temp = info.getValue();
          const getColorClass = (temperature: number) => {
            if (temperature < 36.0) return 'text-blue-600 bg-blue-50';
            if (temperature > 37.5) return 'text-red-600 bg-red-50';
            return 'text-green-600 bg-green-50';
          };
          
          return (
            <span className={`font-bold px-3 py-1 rounded-full text-sm ${getColorClass(temp)}`}>
              {temp.toFixed(1)}°C
            </span>
          );
        },
        sortingFn: 'basic',
      }),
      columnHelper.display({
        id: 'trend',
        header: 'トレンド',
        cell: (info) => {
          const currentTemp = info.row.original.temperature;
          const prevRowIndex = info.row.index + 1;
          const prevRow = data[prevRowIndex];
          
          if (!prevRow) return <span className="text-gray-400">-</span>;
          
          const prevTemp = prevRow.temperature;
          const diff = currentTemp - prevTemp;
          
          if (Math.abs(diff) < 0.1) {
            return <span className="text-gray-500">→</span>;
          }
          
          return (
            <div className="flex items-center space-x-1">
              <span className={diff > 0 ? 'text-red-500' : 'text-blue-500'}>
                {diff > 0 ? '↗' : '↘'}
              </span>
              <span className="text-xs text-gray-600">
                {diff > 0 ? '+' : ''}{diff.toFixed(1)}
              </span>
            </div>
          );
        },
      }),
      columnHelper.display({
        id: 'actions',
        header: 'アクション',
        cell: (info) => (
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              // 詳細表示機能（将来実装）
              console.log('Show details for:', info.row.original);
            }}
          >
            詳細
          </Button>
        ),
      }),
    ],
    [data]
  );

  const table = useReactTable({
    data,
    columns,
    state: {
      sorting,
      pagination: {
        pageIndex,
        pageSize,
      },
    },
    pageCount: Math.ceil(totalCount / pageSize),
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    manualPagination: true,
  });

  const totalPages = Math.ceil(totalCount / pageSize);

  return (
    <div className="space-y-4">
      {/* テーブル */}
      <div className="bg-white shadow rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              {table.getHeaderGroups().map((headerGroup) => (
                <tr key={headerGroup.id}>
                  {headerGroup.headers.map((header) => (
                    <th
                      key={header.id}
                      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                    >
                      {header.isPlaceholder ? null : (
                        <div
                          className={`flex items-center space-x-1 ${
                            header.column.getCanSort() ? 'cursor-pointer select-none' : ''
                          }`}
                          onClick={header.column.getToggleSortingHandler()}
                        >
                          {flexRender(header.column.columnDef.header, header.getContext())}
                          {{
                            asc: <span className="text-blue-500">↗</span>,
                            desc: <span className="text-blue-500">↘</span>,
                          }[header.column.getIsSorted() as string] ?? (
                            header.column.getCanSort() ? (
                              <span className="text-gray-400">↕</span>
                            ) : null
                          )}
                        </div>
                      )}
                    </th>
                  ))}
                </tr>
              ))}
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {isLoading ? (
                <tr>
                  <td colSpan={columns.length} className="px-6 py-12 text-center">
                    <LoadingSpinner size="lg" />
                  </td>
                </tr>
              ) : data.length === 0 ? (
                <tr>
                  <td colSpan={columns.length} className="px-6 py-12 text-center text-gray-500">
                    <div className="space-y-2">
                      <p>該当するデータが見つかりませんでした</p>
                      <p className="text-sm">フィルター条件を変更してみてください</p>
                    </div>
                  </td>
                </tr>
              ) : (
                table.getRowModel().rows.map((row) => (
                  <tr key={row.id} className="hover:bg-gray-50">
                    {row.getVisibleCells().map((cell) => (
                      <td key={cell.id} className="px-6 py-4 whitespace-nowrap">
                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                      </td>
                    ))}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* ページネーション */}
      <div className="flex items-center justify-between bg-white px-4 py-3 border rounded-lg">
        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-700">
            {totalCount > 0 ? (
              <>
                {pageIndex * pageSize + 1} - {Math.min((pageIndex + 1) * pageSize, totalCount)} 件を表示
                （全 {totalCount.toLocaleString()} 件）
              </>
            ) : (
              '0件'
            )}
          </span>
        </div>

        <div className="flex items-center space-x-2">
          {/* ページサイズ選択 */}
          <select
            value={pageSize}
            onChange={(e) => onPageSizeChange(Number(e.target.value))}
            className="px-3 py-1 border border-gray-300 rounded text-sm"
            disabled={isLoading}
          >
            <option value={25}>25件</option>
            <option value={50}>50件</option>
            <option value={100}>100件</option>
            <option value={200}>200件</option>
          </select>

          {/* ページネーションボタン */}
          <div className="flex space-x-1">
            <Button
              variant="outline"
              size="sm"
              onClick={() => onPageChange(0)}
              disabled={pageIndex === 0 || isLoading}
            >
              最初
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              onClick={() => onPageChange(pageIndex - 1)}
              disabled={pageIndex === 0 || isLoading}
            >
              前へ
            </Button>

            <span className="px-3 py-1 text-sm text-gray-700">
              {pageIndex + 1} / {totalPages}
            </span>

            <Button
              variant="outline"
              size="sm"
              onClick={() => onPageChange(pageIndex + 1)}
              disabled={pageIndex >= totalPages - 1 || isLoading}
            >
              次へ
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              onClick={() => onPageChange(totalPages - 1)}
              disabled={pageIndex >= totalPages - 1 || isLoading}
            >
              最後
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};