// src/services/api.ts - プロキシ対応版

import axios from 'axios';

// 開発環境では /api プレフィックスを使用（プロキシ経由）
// 本番環境では直接バックエンドURLを使用
const BASE_URL = process.env.NODE_ENV === 'production' 
  ? 'http://localhost:8000'  // 本番環境（直接）
  : '/api';                  // 開発環境（プロキシ経由）

export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 10000,
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
    if (error.response?.status === 401) {
      // 認証エラー時はログアウト
      localStorage.removeItem('access_token');
      localStorage.removeItem('user_info');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// デフォルトエクスポート（既存コードとの互換性のため）
export default api;