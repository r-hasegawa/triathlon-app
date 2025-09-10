import React from 'react';
import { Header } from './Header';

interface LayoutProps {
  children: React.ReactNode;
  maxWidth?: 'full' | 'container' | 'narrow' | 'wide';
  className?: string;
}

export const Layout: React.FC<LayoutProps> = ({ 
  children, 
  maxWidth = 'container',
  className = ''
}) => {
  // maxWidthクラスを動的に決定
  const getMaxWidthClass = (maxWidth: string) => {
    switch (maxWidth) {
      case 'full':
        return 'max-w-none'; // 制限なし
      case 'narrow':
        return 'max-w-4xl'; // 狭い（56rem）
      case 'wide':
        return 'max-w-full px-4'; // 画面幅いっぱい
      case 'container':
      default:
        return 'container'; // 新しいcontainerクラスを使用
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Header />
      
      <main className={`flex-1 ${className}`}>
        <div className={`mx-auto py-6 sm:py-8 ${getMaxWidthClass(maxWidth)}`}>
          <div className="animate-fadeIn">
            {children}
          </div>
        </div>
      </main>
      
      <footer className="border-t border-gray-200 bg-white mt-auto no-print">
        <div className="container mx-auto py-4">
          <div className="text-center text-sm text-gray-500">
            <p>&copy; 2025 トライアスロンセンサデータシステム</p>
          </div>
        </div>
      </footer>
    </div>
  );
};