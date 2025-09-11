import React, { useState, useEffect } from 'react';
import { Layout } from '@/components/layout/Layout';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

interface User {
  user_id: string;
  name: string;
  email: string;
  created_at: string;
}

export const UserManagement: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [csvFile, setCsvFile] = useState<File | null>(null);

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    setIsLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:8000/admin/users', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      const data = await response.json();
      setUsers(data.users || []);
    } catch (error) {
      console.error('Failed to load users:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const uploadUsersCsv = async () => {
    if (!csvFile) return;

    try {
      const formData = new FormData();
      formData.append('file', csvFile);

      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:8000/admin/users/upload', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      if (response.ok) {
        setCsvFile(null);
        loadUsers();
      }
    } catch (error) {
      console.error('Failed to upload users CSV:', error);
    }
  };

  return (
    <Layout>
      <div className="space-y-6">
        <h1 className="text-2xl font-bold">ユーザー管理</h1>
        
        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4">ユーザー一括登録</h2>
          <div className="space-y-4">
            <Input
              type="file"
              accept=".csv"
              onChange={(e) => setCsvFile(e.target.files?.[0] || null)}
            />
            <Button
              onClick={uploadUsersCsv}
              disabled={!csvFile}
            >
              CSVアップロード
            </Button>
          </div>
        </Card>

        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4">ユーザー一覧</h2>
          {isLoading ? (
            <LoadingSpinner />
          ) : (
            <div className="space-y-2">
              {users.map((user) => (
                <div key={user.user_id} className="p-4 border rounded">
                  <h3 className="font-semibold">{user.name}</h3>
                  <p className="text-sm text-gray-600">{user.email}</p>
                  <p className="text-xs text-gray-500">ID: {user.user_id}</p>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </Layout>
  );
};