import api from './api';
import { 
  DetectionDocument, 
  PaginatedDetections, 
  SurfaceTypeList, 
  DetectionDeleted,
  DetectionFilters 
} from '../types';


export const detectionService = {
  /**
   * Fetches available surface types to populate upload forms dynamically.
   * Public endpoint, no JWT required.
   */
  getSurfaceTypes: async (): Promise<SurfaceTypeList> => {

    const response = await api.get<SurfaceTypeList>('/detections/surface-types');
    return response.data;
  },

  /**
   * Retrieves a paginated list of all detections for the authenticated user.
   * Supports filtering by surface type and severity.
   */
  listDetections: async (filters: DetectionFilters = {}): Promise<PaginatedDetections> => {

    const response = await api.get<PaginatedDetections>('/detections', {

      params: {

        page: filters.page || 1,
        page_size: filters.pageSize || 10,
        surface_type: filters.surfaceType,
        severity: filters.severity,
      }
    });

    return response.data;
  },

  /**
   * Fetches the detection document associated with a specific image.
   * Returns null if the image has not been analyzed yet.
   */
  getDetectionByImageId: async (imageId: string): Promise<DetectionDocument | null> => {

    const response = await api.get<DetectionDocument | null>(`/detections/image/${imageId}`);
    
    return response.data;
  },

  /**
   * Retrieves a paginated list of all detections linked to a specific location.
   * Ideal for location-based structural health monitoring.
   */
  getDetectionsByLocationId: async (
    locationId: string, 
    page: number = 1, 
    pageSize: number = 10
  ): Promise<PaginatedDetections> => {

    const response = await api.get<PaginatedDetections>(`/detections/location/${locationId}`, {
      params: { 

        page, 
        page_size: pageSize 
      }

    });
    return response.data;
  },

  /**
   * Fetches a single detection document by its unique ID.
   */
  getDetectionById: async (detectionId: string): Promise<DetectionDocument> => {

    const response = await api.get<DetectionDocument>(`/detections/${detectionId}`);
    return response.data;
  },

  /**
   * Permanently deletes a detection record and resets the parent image to 'pending'.
   * Backend returns HTTP 410 Gone on success.
   */
  deleteDetection: async (detectionId: string): Promise<DetectionDeleted> => {

    const response = await api.delete<DetectionDeleted>(`/detections/${detectionId}`);
    return response.data;
    
  }
};