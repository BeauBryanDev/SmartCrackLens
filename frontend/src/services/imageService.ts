import api from './api';
import { 
  ImageDoc, 
  PaginatedImages, 
  ImagePatchUpdate, 
  ImageDeleted, 
  UploadInferenceResponse,
  ImageFilters 
} from '../types';

export const imageService = {
  /**
   * Uploads a raw image file and triggers the ONNX inference pipeline.
   * Uses FormData to match FastAPI's UploadFile and Form dependencies.
   * * @param file - The raw image file (JPEG, PNG, WEBP)
   * @param surfaceType - The type of surface (e.g., 'wall', 'concrete')
   * @param locationId - Optional MongoDB ObjectId for the location
   */
  uploadAndAnalyze: async (
    file: File, 
    surfaceType: string, 
    locationId?: string
  ): Promise<UploadInferenceResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('surface_type', surfaceType);
    
    if (locationId) {
      formData.append('location_id', locationId);
    }

    // Axios automatically sets the correct multipart boundary headers 
    // when a FormData object is passed as the payload.
    const response = await api.post<UploadInferenceResponse>('/images/upload', formData);
    return response.data;
  },

  /**
   * Retrieves a paginated list of user images with optional filters.
   */
  listImages: async (filters: ImageFilters = {}): Promise<PaginatedImages> => {
    const response = await api.get<PaginatedImages>('/images', {
      params: {
        page: filters.page || 1,
        page_size: filters.pageSize || 10,
        inference_status: filters.inferenceStatus,
        location_id: filters.locationId,
      }
    });
    return response.data;
  },

  /**
   * Fetches a single ImageDocument by its ID.
   */
  getImageById: async (imageId: string): Promise<ImageDoc> => {
    const response = await api.get<ImageDoc>(`/images/${imageId}`);
    return response.data;
  },

  /**
   * Updates the location association of an existing image.
   */
  patchImage: async (imageId: string, payload: ImagePatchUpdate): Promise<ImageDoc> => {
    const response = await api.patch<ImageDoc>(`/images/${imageId}`, payload);
    return response.data;
  },

  /**
   * Permanently deletes an image, its detections, and physical files.
   */
  deleteImage: async (imageId: string): Promise<ImageDeleted> => {
    const response = await api.delete<ImageDeleted>(`/images/${imageId}`);
    return response.data;
  },

  /**
   * Fetches the annotated output JPEG file as a binary Blob.
   * Crucial for authenticated image rendering in the HUD.
   * * @returns Blob representing the image bytes
   */
  getOutputImageBlob: async (imageId: string): Promise<Blob> => {
    const response = await api.get(`/images/${imageId}/output`, {
      responseType: 'blob', // Tells Axios to not parse this as JSON
    });
    return response.data;
  }
};