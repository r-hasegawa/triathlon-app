import React from 'react';
import { Card } from '@/components/ui/Card';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

interface UploadProgressProps {
  isUploading: boolean;
  progress?: number;
  status?: string;
}

export const UploadProgress: React.FC<UploadProgressProps> = ({
  isUploading,
  progress = 0,
  status = 'アップロード中...'
}) => {
  if (!isUploading) return null;

  return (
    <Card>
      <div className="text-center space-y-4">
        <LoadingSpinner size="lg" />
        <div>
          <p className="text-lg font-medium text-gray-900">{status}</p>
          {progress > 0 && (
            <div className="mt-2">
              <div className="bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <p className="text-sm text-gray-500 mt-1">{progress}% 完了</p>
            </div>
          )}
        </div>
      </div>
    </Card>
  );
};