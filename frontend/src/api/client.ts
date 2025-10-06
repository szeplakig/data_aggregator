// API client using Axios
import axios from 'axios';
import type { Source, DataResponse, DataQueryParams } from '../types/api';

// Configure base URL - will work with Nginx proxy
const API_BASE_URL = '/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// API functions
export const api = {
  // Get all data sources
  getSources: async (enabledOnly: boolean = false): Promise<Source[]> => {
    const response = await apiClient.get<Source[]>('/sources', {
      params: { enabled_only: enabledOnly },
    });
    return response.data;
  },

  // Get data from a specific source
  getData: async (
    sourceName: string,
    params?: DataQueryParams
  ): Promise<DataResponse> => {
    const response = await apiClient.get<DataResponse>(`/data/${sourceName}`, {
      params,
    });
    return response.data;
  },

  // Trigger immediate fetch
  triggerFetch: async (sourceName: string): Promise<void> => {
    await apiClient.post(`/fetch/${sourceName}`);
  },

  // Trigger fetch for all sources
  triggerFetchAll: async (): Promise<void> => {
    await apiClient.post('/fetch-all');
  },
};

export default apiClient;
