// Generic aggregates panel component
import type { Aggregate } from '../types/api';

interface FieldMeta {
  unit?: string;
  format?: string; // e.g. "{:.2f}" from backend
  aggregates?: string[];
  display_name?: string;
  [key: string]: any;
}

interface AggregatesPanelProps {
  aggregates: Record<string, Aggregate>;
  field_metadata?: Record<string, FieldMeta>;
}

function friendlyLabel(key: string): string {
  switch (key) {
    case 'avg':
      return 'Average';
    case 'min':
      return 'Minimum';
    case 'max':
      return 'Maximum';
    case 'sum':
      return 'Sum';
    case 'count':
      return 'Count';
    default:
      return key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
  }
}

export function AggregatesPanel({ aggregates, field_metadata }: AggregatesPanelProps) {
  const fields = Object.keys(aggregates);
  console.log(fields);
  

  if (fields.length === 0) {
    return null;
  }

  return (
    <div className="p-4 bg-white rounded-lg shadow">
      <h3 className="text-lg font-bold mb-4">Statistics</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {fields.map((field) => {
          const stats = aggregates[field];
          console.log(field, stats);
          return (
            <div key={field} className="p-4 border border-gray-200 rounded-lg">
              <h4 className="font-semibold text-sm uppercase text-gray-600 mb-3">
                {field.replace(/_/g, ' ')}
              </h4>
              <div className="space-y-2">
                {Object.keys(stats).map((k) => {
                  const meta = field_metadata?.[field];
                  // choose decimals: if backend provided format like '{:.1f}' try to infer decimals
                  // Count should always be an integer
                  let decimals = k === 'count' ? 0 : 2;
                  if (k !== 'count' && meta?.format) {
                    const m = meta.format.match(/\{:\.(\d+)f\}/);
                    if (m) decimals = parseInt(m[1], 10);
                  }

                  const unit = meta?.unit ? ` ${meta.unit}` : '';

                  return (
                    <StatRow
                      key={k}
                      label={friendlyLabel(k)}
                      value={stats[k]}
                      decimals={decimals}
                      suffix={unit}
                    />
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function StatRow({
  label,
  value,
  decimals = 2,
  suffix = '',
}: {
  label: string;
  value?: number;
  decimals?: number;
  suffix?: string;
}) {
  if (label === 'Count') {
    suffix = '';
    decimals = 0;
  }
  const formatted =
    value === null || value === undefined
      ? '-'
      : value.toLocaleString(undefined, {
          minimumFractionDigits: decimals,
          maximumFractionDigits: decimals,
        });

  return (
    <div className="flex justify-between items-center text-sm">
      <span className="text-gray-600">{label}:</span>
      <span className="font-mono font-medium">{formatted}{suffix}</span>
    </div>
  );
}
