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
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

export interface UserInfo {
  id: number;
  user_id: string;
  username: string;
  full_name: string | null;
  email: string | null;
  is_active: boolean;
  created_at: string;
  sensor_count?: number;
  last_data_at?: string;
}

interface UserTableProps {
  users: UserInfo[];
  isLoading: boolean;
  onEdit: (user: UserInfo) => void;
  onDelete: (user: UserInfo) => void;
  onViewData: (user: UserInfo) => void;
  onResetPassword: (user: UserInfo) => void;
}

const columnHelper = createColumnHelper<UserInfo>();

export const UserTable: React.FC<UserTableProps> = ({
  users,
  isLoading,
  onEdit,
  onDelete,
  onViewData,
  onResetPassword,
}) => {
  const [sorting, setSorting] = React.useState<SortingState>([
    { id: 'created_at', desc: true }
  ]);

  const columns = useMemo(
    () => [
      columnHelper.accessor('user_id', {
        header: 'ユーザーID',
        cell: (info) => (
          <div className="font-mono text-sm bg-gray-100 px-2 py-1 rounded">
            {info.getValue()}
          </div>
        ),
      }),
      columnHelper.accessor('username', {
        header: 'ユーザー名',
        cell: (info) => (
          <div className="font-medium text-gray-900">
            {info.getValue()}
          </div>
        ),
      }),
      columnHelper.accessor('full_name', {
        header: 'フルネーム',
        cell: (info) => (
          <div className="text-gray-900">
            {info.getValue() || <span className="text-gray-400">未設定</span>}
          </div>
        ),
      }),
      columnHelper.accessor('email', {
        header: 'メールアドレス',
        cell: (info) => (
          <div className="text-gray-600 text-sm">
            {info.getValue() || <span className="text-gray-400">未設定</span>}
          </div>
        ),
      }),
      columnHelper.accessor('is_active', {
        header: 'ステータス',
        cell: (info) => (
          <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
            info.getValue() 
              ? 'bg-green-100 text-green-800' 
              : 'bg-red-100 text-red-800'
          }`}>
            {info.getValue() ? 'アクティブ' : '無効'}
          </span>
        ),
      }),
      columnHelper.accessor('sensor_count', {
        header: 'センサー数',
        cell: (info) => {
          const count = info.getValue();
          return (
            <div className="text-center">
              {count !== undefined ? (
                <span className={`font-bold ${count > 0 ? 'text-blue-600' : 'text-gray-400'}`}>
                  {count}
                </span>
              ) : (
                <span className="text-gray-400">-</span>
              )}
            </div>
          );
        },
      }),
      columnHelper.accessor('created_at', {
        header: '作成日',
        cell: (info) => (
          <div className="text-sm text-gray-500">
            {new Date(info.getValue()).toLocaleDateString('ja-JP')}
          </div>
        ),
        sortingFn: 'datetime',
      }),
      columnHelper.accessor('last_data_at', {
        header: '最終データ',
        cell: (info) => {
          const lastData = info.getValue();
          if (!lastData) return <span className="text-gray-400 text-sm">データなし</span>;
          
          const date = new Date(lastData);
          const now = new Date();
          const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
          
          return (
            <div className="text-sm">
              <div className={diffDays <= 7 ? 'text-green-600' : 'text-gray-500'}>
                {date.toLocaleDateString('ja-JP')}
              </div>
              <div className="text-xs text-gray-400">
                {diffDays === 0 ? '今日' : `${diffDays}日前`}
              </div>
            </div>
          );
        },
      }),
      columnHelper.display({
        id: 'actions',
        header: 'アクション',
        cell: (info) => (
          <div className="flex space-x-1">
            <Button
              variant="outline"
              size="sm"
              onClick={() => onEdit(info.row.original)}
            >
              編集
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onViewData(info.row.original)}
              disabled={!info.row.original.sensor_count}
            >
              データ
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onResetPassword(info.row.original)}
            >
              PW
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onDelete(info.row.original)}
              className="text-red-600 hover:text-red-700"
            >
              削除
            </Button>
          </div>
        ),
      }),
    ],
    [onEdit, onDelete, onViewData, onResetPassword]
  );

  const table = useReactTable({
    data: users,
    columns,
    state: {
      sorting,
    },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
  });

  return (
    <div className="space-y-4">
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
              ) : users.length === 0 ? (
                <tr>
                  <td colSpan={columns.length} className="px-6 py-12 text-center text-gray-500">
                    <div className="space-y-2">
                      <p>ユーザーが見つかりませんでした</p>
                      <p className="text-sm">新しいユーザーを追加してください</p>
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
      <div className="flex items-center justify-between">
        <div className="text-sm text-gray-700">
          {users.length > 0 && (
            <>
              {table.getState().pagination.pageIndex * table.getState().pagination.pageSize + 1} - 
              {Math.min((table.getState().pagination.pageIndex + 1) * table.getState().pagination.pageSize, users.length)} 件を表示
              （全 {users.length} 件）
            </>
          )}
        </div>

        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
          >
            前へ
          </Button>
          
          <span className="text-sm text-gray-700">
            ページ {table.getState().pagination.pageIndex + 1} / {table.getPageCount()}
          </span>
          
          <Button
            variant="outline"
            size="sm"
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
          >
            次へ
          </Button>
        </div>
      </div>
    </div>
  );
};