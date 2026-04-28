import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

export const authApi = {
  login: async (username: string, password: string) => {
    const { data } = await api.post('/api/auth/login', { username, password });
    if (data.access_token) {
      localStorage.setItem('token', data.access_token);
      localStorage.setItem('user', JSON.stringify(data.user));
    }
    return data;
  },
  
  logout: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  },
  
  getCurrentUser: async () => {
    const token = localStorage.getItem('token');
    if (!token) return null;
    const { data } = await api.get('/api/auth/me', {
      headers: { Authorization: `Bearer ${token}` },
    });
    return data;
  },
};

export const gtkApi = {
  getList: async (params: {
    page?: number;
    page_size?: number;
    regime?: string;
    country_id?: number;
    region_id?: number;
    category_id?: number;
    product_id?: number;
    company_uzb_id?: number;
    company_foreign_id?: number;
    date_from?: string;
    date_to?: string;
    search?: string;
  }) => {
    const { data } = await api.get('/api/gtk', { params });
    return data;
  },
  
  getStats: async () => {
    const { data } = await api.get('/api/gtk/stats');
    return data;
  },
  
  getCountries: async () => {
    const { data } = await api.get('/api/countries');
    return data;
  },
  
  getRegions: async () => {
    const { data } = await api.get('/api/regions');
    return data;
  },
  
  getCategories: async () => {
    const { data } = await api.get('/api/categories');
    return data;
  },
  
  getProducts: async (categoryId?: number, search?: string) => {
    const { data } = await api.get('/api/products', {
      params: { category_id: categoryId, search },
    });
    return data;
  },
  
  getCompaniesUzb: async () => {
    const { data } = await api.get('/api/companies-uzb');
    return data;
  },
  
  getCompaniesForeign: async () => {
    const { data } = await api.get('/api/companies-foreign');
    return data;
  },
};

export default api;
export { API_URL };