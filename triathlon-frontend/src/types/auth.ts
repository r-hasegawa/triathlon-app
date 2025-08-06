export interface User {
  user_id: string;
  username: string;
  full_name: string | null;
  email: string | null;
  is_admin: boolean;
}

export interface Admin {
  admin_id: string;
  username: string;
  full_name: string | null;
  role: string;
  is_admin: boolean;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user_info: User | Admin;
  expires_in: number;
}

export interface AuthState {
  user: User | Admin | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}