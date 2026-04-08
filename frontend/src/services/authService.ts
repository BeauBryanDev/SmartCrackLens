import api from './api';
import { AuthResponse, User } from '../types';

export interface UserCreate {
  email: string;
  username: string;
  password: string;

}

export const authService = {
  /**
   * LOGIN: Autenticación OAuth2 compatible.
   * transform credentials to URLSearchParams (application/x-www-form-urlencoded)
   */
  login: async (email: string, password: string): Promise<AuthResponse> => {
    // match FastAPI  OAuth2
    const params = new URLSearchParams();
    params.append('username', email);  
    params.append('password', password);

 
    const response = await api.post<AuthResponse>('/auth/login', params, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    
    return response.data;
  },

  /**
   * REGISTER: Create a new User
   * JSON (application/json)
   */
  register: async (userData: UserCreate): Promise<User> => {
    const response = await api.post<User>('/auth/register', userData);
    return response.data;
  },

  /**
   * LOGOUT: Client on LOGIC
   * STATELESS JWT 
   */
  logout: () => {
    // Clean client sessioon 
    console.log("[HUD_SYSTEM]: Session terminated successfully.");
  }

};