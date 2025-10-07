// API types
export interface Source {
  id: number;
  name: string;
  type: string;
  description: string | null;
  enabled: boolean;
  meta?: {
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

// Aggregate is dynamic: backend controls which aggregate metrics are present
export type Aggregate = Record<string, number | undefined>;

export interface DataResponse {
  source: string;
  type: string;
  data: DataPoint[];
  aggregates: Record<string, Aggregate>;
  // Optional metadata for fields provided by backend (display name, unit, format, which aggregates to show)
  field_metadata?: Record<
    string,
    {
      unit?: string;
      format?: string; // python-style format like "{:.2f}" or simple JS format hints
      aggregates?: string[];
      display_name?: string;
      [key: string]: any;
    }
  >;
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
