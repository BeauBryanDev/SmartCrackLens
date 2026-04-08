import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User, AuthResponse } from '../types';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  
  // Acciones
  login: (data: AuthResponse) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,

      // Cuando el backend responda OK al POST /login, llamamos a esta función
      login: (data: AuthResponse) => 
        set({
          user: data.user,
          token: data.access_token,
          isAuthenticated: true,
        }),

      // Para el botón de "Desconectar" o cuando el token expire (Error 401)
      logout: () => 
        set({
          user: null,
          token: null,
          isAuthenticated: false,
        }),
    }),
    {
      // Este es el nombre de la llave que se guardará en el Application > Local Storage de tu navegador
      name: 'smartcracklens-auth-storage',
    }
  )
);