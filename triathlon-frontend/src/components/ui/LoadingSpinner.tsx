import React from 'react';
import { clsx } from 'clsx';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
  text?: string;
  variant?: 'primary' | 'secondary' | 'white';
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'md',
  className,
  text,
  variant = 'primary',
}) => {
  const sizeMap = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12',
    xl: 'h-16 w-16',
  };

  const colorMap = {
    primary: 'border-t-primary-600',
    secondary: 'border-t-gray-600',
    white: 'border-t-white',
  };

  return (
    <div className={clsx('flex flex-col items-center justify-center gap-2', className)}>
      <div className="relative">
        <div 
          className={clsx(
            'spinner',
            sizeMap[size],
            colorMap[variant]
          )}
        />
      </div>
      
      {text && (
        <p className={clsx(
          'text-sm font-medium animate-pulse',
          {
            'text-primary-600': variant === 'primary',
            'text-gray-600': variant === 'secondary',
            'text-white': variant === 'white',
          }
        )}>
          {text}
        </p>
      )}
    </div>
  );
};

// プリセットローディングコンポーネント
export const PageLoader: React.FC<{ text?: string }> = ({ 
  text = "読み込み中..." 
}) => (
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