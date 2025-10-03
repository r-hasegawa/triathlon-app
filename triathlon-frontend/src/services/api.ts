// src/services/api.ts - 401エラー完全対応版

import axios from 'axios';

// 環境変数からAPIのベースURLを取得
const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30000, // 30秒（Renderのスリープ対応）
  headers: {
    'Content-Type': 'application/json',
  },
});

// リクエストインターセプター：認証トークン自動付与
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// レスポンスインターセプター：エラーハンドリング
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // 401エラー（認証エラー）の場合
    if (error.response?.status === 401) {
      console.log('🔒 401 Unauthorized - Session expired, redirecting to login...');
      
      // ローカルストレージをクリア
      localStorage.removeItem('access_token');
      localStorage.removeItem('user_info');
      
      // カスタムイベントを発火（AuthContextが購読）
      window.dispatchEvent(new Event('auth:logout'));
      
      // ログインページにリダイレクト
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login';
      }
    }
    
    // その他のエラーはそのまま返す
    return Promise.reject(error);
  }
);

// デフォルトエクスポート（既存コードとの互換性のため）
export default api;