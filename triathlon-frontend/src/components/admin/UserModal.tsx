import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { UserInfo } from '@/components/admin/UserTable';

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