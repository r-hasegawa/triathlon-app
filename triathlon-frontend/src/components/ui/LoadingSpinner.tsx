import React from 'react';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
  text?: string;
  variant?: 'primary' | 'secondary' | 'white';
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'md',
  className = '',
  text,
  variant = 'primary',
}) => {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12',
    xl: 'h-16 w-16',
  };

  const colorClasses = {
    primary: 'text-blue-600',
    secondary: 'text-gray-600',
    white: 'text-white',
  };

  const spinnerSize = sizeClasses[size];
  const spinnerColor = colorClasses[variant];

  return (
    <div className={`flex flex-col items-center justify-center space-y-2 ${className}`}>
      <div className="relative">
        {/* 外側の円（背景） */}
        <div className={`${spinnerSize} rounded-full border-2 border-gray-200`}></div>
        
        {/* 内側の円（アニメーション） */}
        <div className={`${spinnerSize} rounded-full border-2 border-transparent border-t-current ${spinnerColor} animate-spin absolute top-0 left-0`}></div>
      </div>
      
      {text && (
        <p className={`text-sm font-medium ${spinnerColor} animate-pulse`}>
          {text}
        </p>
      )}
    </div>
  );
};

// プリセットローディングコンポーネント
export const PageLoader: React.FC<{ text?: string }> = ({ text = "読み込み中..." }) => (
  <div className="min-h-screen bg-gray-50 flex items-center justify-center">
    <LoadingSpinner size="lg" text={text} />
  </div>
);

export const InlineLoader: React.FC<{ text?: string }> = ({ text }) => (
  <div className="flex items-center justify-center py-8">
    <LoadingSpinner size="md" text={text} />
  </div>
);

export const ButtonLoader: React.FC = () => (
  <LoadingSpinner size="sm" variant="white" className="mr-2" />
);