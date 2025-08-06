// src/components/admin/UserTable.tsx
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

// src/components/admin/UserModal.tsx
import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { UserInfo } from './UserTable';

interface UserModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (userData: UserFormData) => Promise<void>;
  editingUser?: UserInfo | null;
  isLoading?: boolean;
}

export interface UserFormData {
  user_id: string;
  username: string;
  full_name: string;
  email: string;
  password?: string;
  is_active: boolean;
}

export const UserModal: React.FC<UserModalProps> = ({
  isOpen,
  onClose,
  onSave,
  editingUser,
  isLoading = false,
}) => {
  const [formData, setFormData] = useState<UserFormData>({
    user_id: '',
    username: '',
    full_name: '',
    email: '',
    password: '',
    is_active: true,
  });

  const [errors, setErrors] = useState<{ [key: string]: string }>({});
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (editingUser) {
      setFormData({
        user_id: editingUser.user_id,
        username: editingUser.username,
        full_name: editingUser.full_name || '',
        email: editingUser.email || '',
        is_active: editingUser.is_active,
      });
    } else {
      setFormData({
        user_id: '',
        username: '',
        full_name: '',
        email: '',
        password: '',
        is_active: true,
      });
    }
    setErrors({});
  }, [editingUser, isOpen]);

  if (!isOpen) return null;

  const validateForm = () => {
    const newErrors: { [key: string]: string } = {};

    if (!formData.user_id.trim()) {
      newErrors.user_id = 'ユーザーIDは必須です';
    } else if (!/^[a-zA-Z0-9_]{3,20}$/.test(formData.user_id)) {
      newErrors.user_id = 'ユーザーIDは3-20文字の英数字とアンダースコアのみ使用可能です';
    }

    if (!formData.username.trim()) {
      newErrors.username = 'ユーザー名は必須です';
    } else if (formData.username.length < 3) {
      newErrors.username = 'ユーザー名は3文字以上で入力してください';
    }

    if (formData.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = '有効なメールアドレスを入力してください';
    }

    if (!editingUser && !formData.password) {
      newErrors.password = 'パスワードは必須です';
    } else if (formData.password && formData.password.length < 6) {
      newErrors.password = 'パスワードは6文字以上で入力してください';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsSaving(true);
    try {
      await onSave(formData);
      onClose();
    } catch (error: any) {
      setErrors({ submit: error.message || 'ユーザーの保存に失敗しました' });
    } finally {
      setIsSaving(false);
    }
  };

  const updateFormData = (key: keyof UserFormData, value: string | boolean) => {
    setFormData(prev => ({ ...prev, [key]: value }));
    // エラーをクリア
    if (errors[key]) {
      setErrors(prev => ({ ...prev, [key]: '' }));
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-90vh overflow-y-auto">
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-bold text-gray-900">
              {editingUser ? 'ユーザー編集' : '新規ユーザー作成'}
            </h2>
            <Button variant="outline" onClick={onClose} disabled={isSaving}>
              ✕
            </Button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                label="ユーザーID *"
                type="text"
                value={formData.user_id}
                onChange={(e) => updateFormData('user_id', e.target.value)}
                error={errors.user_id}
                placeholder="例: user001"
                disabled={isSaving || !!editingUser}
                helperText={editingUser ? "ユーザーIDは編集できません" : "3-20文字の英数字とアンダースコア"}
              />

              <Input
                label="ユーザー名 *"
                type="text"
                value={formData.username}
                onChange={(e) => updateFormData('username', e.target.value)}
                error={errors.username}
                placeholder="例: testuser1"
                disabled={isSaving}
              />
            </div>

            <Input
              label="フルネーム"
              type="text"
              value={formData.full_name}
              onChange={(e) => updateFormData('full_name', e.target.value)}
              error={errors.full_name}
              placeholder="例: 田中 太郎"
              disabled={isSaving}
            />

            <Input
              label="メールアドレス"
              type="email"
              value={formData.email}
              onChange={(e) => updateFormData('email', e.target.value)}
              error={errors.email}
              placeholder="例: user@example.com"
              disabled={isSaving}
            />

            <Input
              label={editingUser ? "新しいパスワード" : "パスワード *"}
              type="password"
              value={formData.password || ''}
              onChange={(e) => updateFormData('password', e.target.value)}
              error={errors.password}
              placeholder={editingUser ? "変更する場合のみ入力" : "6文字以上"}
              disabled={isSaving}
              helperText={editingUser ? "空白の場合はパスワードを変更しません" : ""}
            />

            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-700">
                ステータス
              </label>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={formData.is_active}
                  onChange={(e) => updateFormData('is_active', e.target.checked)}
                  disabled={isSaving}
                  className="mr-2"
                />
                アクティブ（ログイン可能）
              </label>
            </div>

            {errors.submit && (
              <div className="bg-red-50 border border-red-200 rounded-md p-3">
                <p className="text-sm text-red-600">{errors.submit}</p>
              </div>
            )}

            <div className="flex justify-end space-x-3 pt-4 border-t">
              <Button
                type="button"
                variant="outline"
                onClick={onClose}
                disabled={isSaving}
              >
                キャンセル
              </Button>
              
              <Button
                type="submit"
                disabled={isSaving}
                isLoading={isSaving}
              >
                {isSaving ? '保存中...' : editingUser ? '更新' : '作成'}
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};