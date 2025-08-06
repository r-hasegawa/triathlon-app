import React from 'react';
import { Header } from './Header';

interface LayoutProps {
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Header />
      
      <main className="flex-1">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
          <div className="animate-fadeIn">
            {children}
          </div>
        </div>
      </main>
      
      {/* フッター（必要に応じて） */}
      <footer className="bg-white border-t border-gray-200 mt-auto no-print">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="text-center text-sm text-gray-500">
            <p>&copy; 2025 トライアスロンセンサデータシステム</p>
          </div>
        </div>
      </footer>
    </div>
  );
};