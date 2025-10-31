import api from './api';

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}

export interface UserResponse {
  id: number;
  username: string;
  email: string;
  role: string;
  is_active: boolean;
  created_at: string;
  last_login_at: string | null;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export const authService = {
  async login(credentials: LoginRequest): Promise<{ token: string; user: UserResponse }> {
    try {
      const response = await api.post<{access_token: string; token_type: string; user: UserResponse}>('/auth/login', credentials);
      
      return { 
        token: response.data.access_token, 
        user: response.data.user 
      };
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Login failed');
    }
  },

  async register(userData: RegisterRequest): Promise<{ token: string; user: UserResponse }> {
    try {
      // First register the user
      const userResponse = await api.post<UserResponse>('/users', userData);
      const user = userResponse.data;
      
      // Then login to get token
      const loginResponse = await this.login({
        username: userData.username,
        password: userData.password
      });
      
      return loginResponse;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Registration failed');
    }
  },

  async getCurrentUser(): Promise<UserResponse> {
    try {
      // Use the /users/me endpoint
      const response = await api.get<UserResponse>('/users/me');
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to get user info');
    }
  },

  async updateUser(userId: number, userData: Partial<UserResponse>): Promise<UserResponse> {
    try {
      const response = await api.put<UserResponse>(`/users/${userId}`, userData);
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to update user');
    }
  }
};

