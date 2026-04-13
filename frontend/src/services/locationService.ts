import api from './api';
import { 
  Location, 
  LocationCreate, 
  LocationFullUpdate, 
  LocationPatchUpdate, 
  PaginatedLocations, 
  LocationDeleted 
} from '../types';

export const locationService = {
  /**
   * Creates a new inspection location.
   * User ID is handled securely by the backend via JWT.
   */
  createLocation: async (payload: LocationCreate): Promise<Location> => {
    
    const response = await api.post<Location>('/locations', payload);
    return response.data;
  },

  /**
   * Retrieves a paginated list of locations owned by the authenticated user.
   */
  listLocations: async (page: number = 1, pageSize: number = 10): Promise<PaginatedLocations> => {
    const response = await api.get<PaginatedLocations>('/locations', {

      params: { 
        page, 
        page_size: pageSize 
      }
    });
    return response.data;
  },

  /**
   * Fetches a specific location document by its ID.
   */
  getLocationById: async (locationId: string): Promise<Location> => {

    const response = await api.get<Location>(`/locations/${locationId}`);
    return response.data;
  },

  /**
   * Completely replaces a location document's editable fields.
   */
  fullUpdate: async (locationId: string, payload: LocationFullUpdate): Promise<Location> => {

    const response = await api.put<Location>(`/locations/${locationId}`, payload);
    return response.data;
  },

  /**
   * Partially updates specific fields in a location document.
   */
  patchUpdate: async (locationId: string, payload: LocationPatchUpdate): Promise<Location> => {

    const response = await api.patch<Location>(`/locations/${locationId}`, payload);
    return response.data;
  },

  /**
   * Permanently deletes a location from the database.
   * Backend returns HTTP 410 Gone on success.
   */
  deleteLocation: async (locationId: string): Promise<LocationDeleted> => {

    const response = await api.delete<LocationDeleted>(`/locations/${locationId}`);
    return response.data;
  }
};


