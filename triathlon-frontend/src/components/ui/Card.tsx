import React from 'react';
import { clsx } from 'clsx';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  title?: string;
  subtitle?: string;
  onClick?: () => void;
}

export const Card: React.FC<CardProps> = ({
  children,
  className,
  title,
  subtitle,
  onClick,
}) => {
  return (
    <div 
      className={clsx(
        'card',
        {
          'cursor-pointer hover:shadow-md transition-shadow duration-200': onClick,
        },
        className
      )}
      onClick={onClick}
    >
      {(title || subtitle) && (
        <div className="card-header">
          {title && (
            <h3 className="text-lg font-semibold text-gray-900 leading-6">
              {title}
            </h3>
          )}
          {subtitle && (
            <p className="mt-1 text-sm text-gray-600">
              {subtitle}
            </p>
          )}
        </div>
      )}
      <div className="card-content">
        {children}
      </div>
    </div>
  );
};