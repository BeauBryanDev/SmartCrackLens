import api from './api';
import { 
  DashboardResponse,
  SummaryStats,
  SeverityDistribution,
  SurfaceDistribution,
  OrientationDistribution,
  DetectionsTimeline,
  TopLocations,
  LatencyHistory
} from '../types';

export const analyticService = {
  /**
   * Fetches the FULL dashboard payload in a single parallelized backend request.
   * Highly optimized for the initial page load of the Command Center.
   * * @param timelineDays - The window in days for the timeline chart.
   */
  getDashboard: async (timelineDays: number = 30): Promise<DashboardResponse> => {

    const response = await api.get<DashboardResponse>('/analytics/dashboard', {
      params: { timeline_days: timelineDays }
    });
    return response.data;
  },

  /**
   * Fetches only the top-level summary statistics cards.
   */
  getSummaryStats: async (): Promise<SummaryStats> => {

    const response = await api.get<SummaryStats>('/analytics/summary');
    return response.data;
  },

  /**
   * Retrieves crack severity distribution for Pie/Donut charts.
   */
  getSeverityDistribution: async (limit: number = 8): Promise<SeverityDistribution> => {

    const response = await api.get<SeverityDistribution>('/analytics/severity', {
      params: { limit }
    });
    return response.data;
  },

  /**
   * Retrieves structural surface type distribution for Bar charts.
   */
  getSurfaceDistribution: async (): Promise<SurfaceDistribution> => {

    const response = await api.get<SurfaceDistribution>('/analytics/surface');
    return response.data;
  },

  /**
   * Retrieves crack orientation data mapped for a Radar chart visualization.
   */
  getOrientationDistribution: async (): Promise<OrientationDistribution> => {

    const response = await api.get<OrientationDistribution>('/analytics/orientation');
    return response.data;
  },

  /**
   * Retrieves historical detection volume over a given number of days.
   */
  getTimeline: async (days: number = 30): Promise<DetectionsTimeline> => {

    const response = await api.get<DetectionsTimeline>('/analytics/timeline', {
      params: { days }
    });
    return response.data;
  },

  /**
   * Retrieves the locations with the highest concentration of detected anomalies.
   */
  getTopLocations: async (limit: number = 8): Promise<TopLocations> => {

    const response = await api.get<TopLocations>('/analytics/locations', {
      params: { limit }
    });
    return response.data;
  },

  /**
   * Retrieves the most recent inference execution times to monitor model performance.
   */
  getLatencyHistory: async (limit: number = 20): Promise<LatencyHistory> => {
    
    const response = await api.get<LatencyHistory>('/analytics/latency', {
      params: { limit }
    });
    return response.data;
  }
};