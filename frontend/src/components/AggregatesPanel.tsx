// Generic aggregates panel component
import type { Aggregate } from '../types/api';

interface AggregatesPanelProps {
  aggregates: Record<string, Aggregate>;
}

export function AggregatesPanel({ aggregates }: AggregatesPanelProps) {
  const fields = Object.keys(aggregates);

  if (fields.length === 0) {
    return null;
  }

  return (
    <div className="p-4 bg-white rounded-lg shadow">
      <h3 className="text-lg font-bold mb-4">Statistics</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {fields.map((field) => {
          const stats = aggregates[field];
          return (
            <div key={field} className="p-4 border border-gray-200 rounded-lg">
              <h4 className="font-semibold text-sm uppercase text-gray-600 mb-3">
                {field.replace(/_/g, ' ')}
              </h4>
              <div className="space-y-2">
                <StatRow label="Average" value={stats.avg} />
                <StatRow label="Minimum" value={stats.min} />
                <StatRow label="Maximum" value={stats.max} />
                <StatRow label="Sum" value={stats.sum} />
                <StatRow label="Count" value={stats.count} decimals={0} />
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
}: {
  label: string;
  value: number;
  decimals?: number;
}) {
  return (
    <div className="flex justify-between items-center text-sm">
      <span className="text-gray-600">{label}:</span>
      <span className="font-mono font-medium">
        {value.toLocaleString(undefined, {
          minimumFractionDigits: decimals,
          maximumFractionDigits: decimals,
        })}
      </span>
    </div>
  );
}
