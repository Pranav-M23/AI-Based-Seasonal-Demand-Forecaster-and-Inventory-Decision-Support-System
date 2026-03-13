import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const dashboardAPI = {
  getMeta: async () => {
    const response = await api.get('/meta');
    return response.data;
  },

  getStoreCategoryForecast: async (storeId, category = 'All') => {
    const params = { store: storeId, category };
    const response = await api.get('/forecast/store-category', { params });
    return response.data;
  },

  getDiscountByRegion: async (region) => {
    const response = await api.get('/discount/region', { params: { region } });
    return response.data;
  },

  getInventorySummary: async () => {
    const response = await api.get('/inventory/exec-summary');
    return response.data;
  },

  getStoreDecisions: async (storeId, category = null) => {
    const params = { store: storeId };
    if (category && category !== 'All') params.category = category;
    const response = await api.get('/inventory/store-decisions', { params });
    return response.data;
  },

  getStoresByRegion: async (region) => {
    const response = await api.get('/stores', { params: { region } });
    return response.data;
  },

  getFestivalsByRegion: async (region, state = null) => {
    const params = {};
    if (state) params.state = state;
    const response = await api.get(`/festivals/region/${encodeURIComponent(region)}`, { params });
    return response.data;
  },
};

// ============================================================================
// PREDICTIONS CATALOG API
// ============================================================================
export const predictionsAPI = {
  create: async (data) => {
    const response = await api.post('/predictions', data);
    return response.data;
  },

  getAll: async (filters = {}) => {
    const response = await api.get('/predictions', { params: filters });
    return response.data;
  },

  getById: async (id) => {
    const response = await api.get(`/predictions/${id}`);
    return response.data;
  },

  update: async (id, data) => {
    const response = await api.put(`/predictions/${id}`, data);
    return response.data;
  },

  delete: async (id) => {
    const response = await api.delete(`/predictions/${id}`);
    return response.data;
  },

  bulkDelete: async (ids) => {
    const response = await api.post('/predictions/bulk-delete', { ids });
    return response.data;
  },

  getStats: async () => {
    const response = await api.get('/predictions/stats');
    return response.data;
  },
};

export default api;