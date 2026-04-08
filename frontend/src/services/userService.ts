import api from './api';
import { 
  User, 
  PaginatedUsers, 
  UserPatchUpdate, 
  UserFullUpdate, 
  UserDeleted 
} from '../types';

export const userService = {
  /**
   * Fetches the profile of the currently authenticated user based on JWT.
   */
  getMe: async (): Promise<User> => {
    const response = await api.get<User>('/users/me');
    return response.data;
  },

  /**
   * Fetches a specific user profile by its unique ID.
   */
  getUserById: async (userId: string): Promise<User> => {
    const response = await api.get<User>(`/users/${userId}`);
    return response.data;
  },

  /**
   * ADMIN ONLY: Retrieves a paginated list of all users in the system.
   * @param page - Current page number
   * @param pageSize - Amount of records per request
   */
  listUsers: async (page: number = 1, pageSize: number = 10): Promise<PaginatedUsers> => {
    const response = await api.get<PaginatedUsers>('/users', {
      params: { 
        page, 
        page_size: pageSize 
      }
    });
    return response.data;
  },

  /**
   * Performs a full update of the user's profile data.
   */
  fullUpdate: async (userId: string, payload: UserFullUpdate): Promise<User> => {
    const response = await api.put<User>(`/users/${userId}`, payload);
    return response.data;
  },
  /**
   * Performs a partial update (PATCH) on specific user fields.
   */
  Update: async (userId: string, payload: UserPatchUpdate): Promise<User> => {
    const response = await api.patch<User>(`/users/${userId}`, payload);
    return response.data;
  },

  /**
   * Triggers account deletion and associated data cleanup.
   * Backend returns HTTP 410 Gone on successful deletion.
   */
  deleteUser: async (userId: string): Promise<UserDeleted> => {
    const response = await api.delete<UserDeleted>(`/users/${userId}`);
    return response.data;
  }
};