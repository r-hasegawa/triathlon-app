import api from './api';
import { LoginRequest, LoginResponse, User, Admin } from '@/types/auth';

export const authService = {
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const formData = new FormData();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);

    const response = await api.post<LoginResponse>('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });

    // トークンとユーザー情報をローカルストレージに保存
    localStorage.setItem('access_token', response.data.access_token);
    localStorage.setItem('user_info', JSON.stringify(response.data.user_info));

    return response.data;
  },

  async getCurrentUser(): Promise<User | Admin> {
    const response = await api.get<User | Admin>('/auth/me');
    return response.data;
  },

  logout(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_info');
  },

  getStoredUser(): User | Admin | null {
    const userInfo = localStorage.getItem('user_info');
    return userInfo ? JSON.parse(userInfo) : null;
  },

  getStoredToken(): string | null {
    return localStorage.getItem('access_token');
  },

  isAuthenticated(): boolean {
    const token = this.getStoredToken();
    const user = this.getStoredUser();
    return !!(token && user);
  }
};