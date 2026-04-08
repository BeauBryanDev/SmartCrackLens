import axios from 'axios';
import { AxiosInstance, InternalAxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';

import { useAuthStore } from '../store/useAuthStore';


const api : AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8001/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use(
  (config : InternalAxiosRequestConfig ) => {
    // Leemos el token directamente del store de Zustand
    const token = useAuthStore.getState().token;
    
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  // ...
);


api.interceptors.response.use(
  (response : AxiosResponse ) => response,
  (error : AxiosError ) => {
    if (error.response?.status === 401) {
      console.error("[HUD_SYSTEM_AUTH]: SESSION_EXPIRED. RE-AUTHENTICATION REQUIRED.");
      // Cerramos sesión limpiamente desde Zustand
      useAuthStore.getState().logout();
    }
    return Promise.reject(error);
  }
);

export default api;