// API types
export interface Source {
  id: number;
  name: string;
  type: string;
  description: string | null;
  enabled: boolean;
  metadata?: {
    location?: string;
    location_coords?: string;
    [key: string]: any;
  } | null;
  created_at: string;
}

export interface DataPoint {
  timestamp: string;
  [key: string]: any;
}

export interface Aggregate {
  avg: number;
  min: number;
  max: number;
  sum: number;
  count: number;
}

export interface DataResponse {
  source: string;
  type: string;
  data: DataPoint[];
  aggregates: Record<string, Aggregate>;
  period: {
    from?: string;
    to?: string;
  };
  total_count: number;
  returned_count: number;
}

export interface DataQueryParams {
  limit?: number;
  offset?: number;
  hours?: number;
}
