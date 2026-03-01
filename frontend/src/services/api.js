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
};

export default api;