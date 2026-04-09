import api from './api';
import { AuthResponse, UserCreate,  User } from '../types';

export interface ActionResponse {

    [key: string]: any; 

}

export const authService = {
  /**
   * LOGIN: Autenticación OAuth2 compatible.
   * transform credentials to URLSearchParams (application/x-www-form-urlencoded)
   */
  login: async (email: string, password: string): Promise<AuthResponse> => {
    // match FastAPI  OAuth2
    const params = new URLSearchParams();
    params.append('username', email);   // OAuth2 expects 'username'
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

  /**
   * CHANGE PASSWORD: Updates the user's password securely.
   * Based on the FastAPI router, it expects query parameters, not a JSON body.
   * * @param currentPassword - The existing password to validate.
   * @param newPassword - The new password complying with system rules.
   */
  changePassword: async (currentPassword: string, newPassword: string): Promise<ActionResponse> => {

    // It pass es 'null' as the body, and send the variables via query params
    const response = await api.patch<ActionResponse>('/auth/change-password', null, {

      params: {
        current_password: currentPassword,
        new_password: newPassword,
      }
    });
    return response.data;
  },

  /**
   * DEACTIVATE: Disables the user account (soft-delete).
   * User is identified automatically via the JWT in the Authorization header.
   */
  deactivateAccount: async (): Promise<ActionResponse> => {
    const response = await api.patch<ActionResponse>('/auth/deactivate');
    return response.data;
  },

  logout: () => {
    // Clean client sessioon 
    console.log("[HUD_SYSTEM]: Session terminated successfully.");
  }

};

