export type Regime = 'ИМ' | 'ЭК';

export interface User {
  id: number;
  username: string;
  email: string;
  full_name: string | null;
  is_admin: number;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface LookupItem {
  id: number;
  name: string;
}

export interface CompanyUzbItem extends LookupItem {
  stir: string;
}

export interface ProductItem extends LookupItem {
  tnved: string;
  category_id: number;
}

export interface GTKRecord {
  id: number;
  regime: Regime;
  country_id: number;
  country_name: string | null;
  address_uz: string | null;
  address_foreign: string | null;
  region_id: number | null;
  region_name: string | null;
  company_uzb_id: number | null;
  company_uzb_name: string | null;
  company_foreign_id: number | null;
  company_foreign_name: string | null;
  product_id: number;
  product_name: string | null;
  category_id: number | null;
  category_name: string | null;
  tnved: string | null;
  unit: string | null;
  weight: number | null;
  quantity: number | null;
  price_thousand: number | null;
  date: string;
}

export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface TopItem {
  id: number;
  name: string;
  count: number;
}

export interface GTKStats {
  total_count: number;
  import_sum: number;
  export_sum: number;
  top_countries: TopItem[];
  top_categories: TopItem[];
}

export interface GTKListParams {
  page?: number;
  page_size?: number;
  regime?: Regime;
  country_id?: number;
  region_id?: number;
  category_id?: number;
  product_id?: number;
  company_uzb_id?: number;
  company_foreign_id?: number;
  date_from?: string;
  date_to?: string;
  search?: string;
}
