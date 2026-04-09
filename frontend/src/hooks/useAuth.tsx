import { useState } from 'react';
import { authService } from '../services/authService';
import { useAuthStore } from '../store/useAuthStore';

export const useAuth = () => {
  // Local UI state for forms
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Extracting actions and state from the global Zustand store
  const setLoginState = useAuthStore((state) => state.login);
  const executeLogout = useAuthStore((state) => state.logout);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const currentUser = useAuthStore((state) => state.user);

  /**
   * Authenticates the user, handles loading UI, and updates the global store.
   * * @param email - User email (acts as username for OAuth2)
   * @param password - User password
   * @returns A boolean indicating success or failure (useful for UI redirects)
   */
  const login = async (email: string, password: string): Promise<boolean> => {
    setIsLoading(true);
    setError(null);

    try {
      const authData = await authService.login(email, password);
      
      // Pass the backend response to Zustand to persist the session
      setLoginState(authData); 
      
      return true; // Success flag
      
    } catch (err: any) {
      console.error('[HUD_AUTH_SYSTEM]: Authentication procedure failed.', err);
      
      // Extract specific error message from FastAPI (usually inside 'detail')
      const errorMessage = err.response?.data?.detail || 'ACCESS DENIED: Invalid credentials.';
      setError(errorMessage);
      
      return false; // Failure flag
      
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Terminates the current session and clears global state.
   */
  const logout = () => {
    executeLogout();
  };

  // Expose everything the UI might need
  return {
    login,
    logout,
    isLoading,
    error,
    isAuthenticated,
    user: currentUser,
  };
};