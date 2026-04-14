import { create } from 'zustand';
import { persist, createJSONStorage, StateStorage } from 'zustand/middleware';
import { User, AuthResponse } from '../types';
import CryptoJS from 'crypto-js';


const ENCRYPTION_KEY = import.meta.env.VITE_STORAGE_KEY || 'development_fallback_key_do_not_use_in_prod';

/**
 * Custom secure storage engine for Zustand.
 * Implements AES-256 symmetric encryption to protect the JWT and user profile.
 */
const secureStorage: StateStorage = {

  getItem: (name: string): string | null => {

    const encryptedStr = localStorage.getItem(name);

    if (!encryptedStr) return null;

    try {
      // Decrypt the string using the secret key
      const bytes = CryptoJS.AES.decrypt(encryptedStr, ENCRYPTION_KEY);
      const decryptedStr = bytes.toString(CryptoJS.enc.Utf8);

      // If decryption yields empty string, the key might be wrong or data corrupted
      if (!decryptedStr) throw new Error("Corrupted or tampered data");

      return decryptedStr;

    } catch (error) {

      console.error('[HUD_SECURITY_BREACH]: Decryption failed. Session purged.');

      localStorage.removeItem(name);

      return null;

    }
  },

  setItem: (name: string, value: string): void => {
    // Encrypt the JSON stringified state before saving
    const encryptedStr = CryptoJS.AES.encrypt(value, ENCRYPTION_KEY).toString();

    localStorage.setItem(name, encryptedStr);
  },

  removeItem: (name: string): void => {

    localStorage.removeItem(name);
  },
};

interface AuthState {

  user: User | null;
  token: string | null;
  isAuthenticated: boolean;

  // Actions
  login: (data: AuthResponse) => void;
  logout: () => void;
  setUser: (user: User) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,

      /**
       * Injects user data and token into the secure state.
       */
      login: (data: AuthResponse) =>
        set({
          user: data.user,
          token: data.access_token,
          isAuthenticated: true,
        }),

      /**
       * Purges the session from memory and encrypted storage.
       */
      logout: () =>
        set({
          user: null,
          token: null,
          isAuthenticated: false,
        }),

      setUser: (user: User) =>
        set({ user }),
    }),
    {
      name: 'sc_lens_secure_session', // The actual key seen in LocalStorage
      storage: createJSONStorage(() => secureStorage), // Inject the AES engine
    }
  )
);
