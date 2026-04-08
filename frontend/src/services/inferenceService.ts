import api from './api';
import { UploadInferenceResponse } from '../types';

export const inferenceService = {
  /**
   * Re-runs the crack detection model on a previously uploaded image.
   * Used for state recovery (failed inferences) or applying updated model weights
   * after a user deletes an existing detection record.
   *
   * @param imageId - The MongoDB ObjectId of the target image.
   * @returns A promise resolving to the fully updated image and detection documents.
   */
  reanalyzeImage: async (imageId: string): Promise<UploadInferenceResponse> => {
    // The endpoint does not require a payload body, just the path parameter
    const response = await api.post<UploadInferenceResponse>(`/inference/reanalyze/${imageId}`);
    return response.data;
  }
  
};