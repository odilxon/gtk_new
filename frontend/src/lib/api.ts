import axios, { AxiosError, AxiosInstance } from 'axios';

import type {
  CompanyUzbItem,
  GTKListParams,
  GTKRecord,
  GTKStats,
  LookupItem,
  LoginResponse,
  Paginated,
  ProductItem,
  User,
} from '@/types/api';
import type {
  ChartFilters,
  ChartGroup,
  ChartRegime,
  GroupBreakdown,
  GroupSummary,
  MonthlyResponse,
  RegionsResponse,
  TopItems,
  WorldResponse,
} from '@/types/charts';

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8005';

const TOKEN_KEY = 'token';
const USER_KEY = 'user';

export const tokenStorage = {
  get: (): string | null =>
    typeof window === 'undefined' ? null : localStorage.getItem(TOKEN_KEY),
  set: (token: string) => {
    if (typeof window !== 'undefined') localStorage.setItem(TOKEN_KEY, token);
  },
  clear: () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(USER_KEY);
    }
  },
  getUser: (): User | null => {
    if (typeof window === 'undefined') return null;
    const raw = localStorage.getItem(USER_KEY);
    if (!raw) return null;
    try {
      return JSON.parse(raw) as User;
    } catch {
      return null;
    }
  },
  setUser: (user: User) => {
    if (typeof window !== 'undefined')
      localStorage.setItem(USER_KEY, JSON.stringify(user));
  },
};

const api: AxiosInstance = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  const token = tokenStorage.get();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail?: string }>) => {
    if (error.response?.status === 401 && typeof window !== 'undefined') {
      tokenStorage.clear();
    }
    const detail = error.response?.data?.detail;
    if (detail) {
      error.message = detail;
    }
    return Promise.reject(error);
  },
);

export const authApi = {
  login: async (username: string, password: string): Promise<LoginResponse> => {
    const { data } = await api.post<LoginResponse>('/api/auth/login', {
      username,
      password,
    });
    tokenStorage.set(data.access_token);
    tokenStorage.setUser(data.user);
    return data;
  },

  logout: () => tokenStorage.clear(),

  me: async (): Promise<User> => {
    const { data } = await api.get<User>('/api/auth/me');
    return data;
  },
};

export const gtkApi = {
  list: async (params: GTKListParams): Promise<Paginated<GTKRecord>> => {
    const { data } = await api.get<Paginated<GTKRecord>>('/api/gtk', { params });
    return data;
  },

  getById: async (id: number): Promise<GTKRecord> => {
    const { data } = await api.get<GTKRecord>(`/api/gtk/${id}`);
    return data;
  },

  stats: async (): Promise<GTKStats> => {
    const { data } = await api.get<GTKStats>('/api/gtk/stats');
    return data;
  },
};

export const lookupsApi = {
  countries: async (): Promise<LookupItem[]> => {
    const { data } = await api.get<LookupItem[]>('/api/countries');
    return data;
  },
  regions: async (): Promise<LookupItem[]> => {
    const { data } = await api.get<LookupItem[]>('/api/regions');
    return data;
  },
  categories: async (): Promise<LookupItem[]> => {
    const { data } = await api.get<LookupItem[]>('/api/categories');
    return data;
  },
  products: async (
    categoryId?: number,
    search?: string,
  ): Promise<ProductItem[]> => {
    const { data } = await api.get<ProductItem[]>('/api/products', {
      params: { category_id: categoryId, search },
    });
    return data;
  },
  companiesUzb: async (): Promise<CompanyUzbItem[]> => {
    const { data } = await api.get<CompanyUzbItem[]>('/api/companies-uzb');
    return data;
  },
  companiesForeign: async (): Promise<LookupItem[]> => {
    const { data } = await api.get<LookupItem[]>('/api/companies-foreign');
    return data;
  },
};

export const chartsApi = {
  years: async (): Promise<number[]> => {
    const { data } = await api.get<number[]>('/api/charts/years');
    return data;
  },
  monthly: async (filters: ChartFilters = {}): Promise<MonthlyResponse> => {
    const { data } = await api.get<MonthlyResponse>('/api/charts/monthly', {
      params: filters,
    });
    return data;
  },
  groupSummary: async (
    year: number,
    group: ChartGroup,
    filters: Pick<ChartFilters, 'region_id' | 'country_id'> = {},
  ): Promise<GroupSummary> => {
    const { data } = await api.get<GroupSummary>('/api/charts/group-summary', {
      params: { year, group, ...filters },
    });
    return data;
  },
  groupBreakdown: async (
    year: number,
    group: ChartGroup,
    type: 'import' | 'export' | 'all' = 'all',
    filters: Pick<ChartFilters, 'region_id' | 'country_id'> = {},
  ): Promise<GroupBreakdown> => {
    const { data } = await api.get<GroupBreakdown>('/api/charts/group-breakdown', {
      params: { year, group, type, ...filters },
    });
    return data;
  },
  topOrganizations: async (
    year: number,
    regime: ChartRegime,
    filters: ChartFilters & { limit?: number } = {},
  ): Promise<TopItems> => {
    const { data } = await api.get<TopItems>('/api/charts/top-organizations', {
      params: { year, regime, ...filters },
    });
    return data;
  },
  topCountries: async (
    year: number,
    regime: ChartRegime,
    filters: ChartFilters & { limit?: number } = {},
  ): Promise<TopItems> => {
    const { data } = await api.get<TopItems>('/api/charts/top-countries', {
      params: { year, regime, ...filters },
    });
    return data;
  },
  regions: async (
    year: number,
    regime: ChartRegime,
    filters: ChartFilters = {},
  ): Promise<RegionsResponse> => {
    const { data } = await api.get<RegionsResponse>('/api/charts/regions', {
      params: { year, regime, ...filters },
    });
    return data;
  },
  world: async (
    year: number,
    regime: ChartRegime,
    filters: ChartFilters = {},
  ): Promise<WorldResponse> => {
    const { data } = await api.get<WorldResponse>('/api/charts/world', {
      params: { year, regime, ...filters },
    });
    return data;
  },
};

export default api;
