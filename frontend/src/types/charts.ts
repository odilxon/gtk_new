export type ChartRegime = 'import' | 'export';
export type ChartGroup = 'meva' | 'oziq';

export interface ChartFilters {
  year?: number;
  tnved?: string[];
  region_id?: number;
  country_id?: number;
}

export interface MonthlyResponse {
  months: string[];
  imports: Record<string, Array<number | null>>;
  exports: Record<string, Array<number | null>>;
  import_grow: Record<string, Array<number | null>>;
  export_grow: Record<string, Array<number | null>>;
}

export interface GroupTotals {
  total: number;
  massa: number;
}

export interface GroupSummary {
  year: number;
  group: ChartGroup;
  import_: GroupTotals;
  export: GroupTotals;
  total: GroupTotals;
}

export interface GroupBreakdownRow {
  name: string;
  massa: number;
  total: number;
  avg: number;
}

export interface GroupBreakdown {
  year: number;
  group: ChartGroup;
  type: 'import' | 'export' | 'all';
  rows: GroupBreakdownRow[];
}

export interface TopItemRow {
  label: string;
  value: number;
}

export interface TopItems {
  year: number;
  items: TopItemRow[];
}

export interface RegionPoint {
  name: string;
  code: string;
  value: number;
  massa: number;
  meva_total: number;
  meva_massa: number;
  oziq_total: number;
  oziq_massa: number;
}

export interface RegionsResponse {
  year: number;
  regime: ChartRegime;
  items: RegionPoint[];
  max_value: number;
}

export interface WorldPoint {
  iso: string;
  name: string;
  name_uz: string | null;
  value: number;
  massa: number;
  meva_value: number;
  meva_massa: number;
  oziq_value: number;
  oziq_massa: number;
}

export interface WorldResponse {
  year: number;
  regime: ChartRegime;
  items: WorldPoint[];
  max_value: number;
}
