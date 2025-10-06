// Generic data table component
import { useState, useMemo } from 'react';
import type { DataPoint } from '../types/api';
import { log } from 'console';

interface DataTableProps {
  data: DataPoint[];
  sourceName: string;
}

export function DataTable({ data, sourceName }: DataTableProps) {
  const [sortField, setSortField] = useState<string>('timestamp');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');

  // Extract all field names dynamically
  const fields = useMemo(() => {
    if (data.length === 0) return [];
    console.log(data);
    
    const allFields = new Set<string>();
    data.forEach((row) => {
      Object.keys(row).forEach((key) => allFields.add(key));
    });
    // Put timestamp first
    const fieldArray = Array.from(allFields);
    console.log(fieldArray);    
    return ['timestamp', ...fieldArray.filter((f) => f !== 'timestamp')];
  }, [data]);

  // Sort data
  const sortedData = useMemo(() => {
    return [...data].sort((a, b) => {
      const aVal = a[sortField];
      const bVal = b[sortField];

      if (aVal === null || aVal === undefined) return 1;
      if (bVal === null || bVal === undefined) return -1;

      let comparison = 0;
      if (typeof aVal === 'string' && typeof bVal === 'string') {
        comparison = aVal.localeCompare(bVal);
      } else {
        comparison = aVal > bVal ? 1 : aVal < bVal ? -1 : 0;
      }

      return sortDirection === 'asc' ? comparison : -comparison;
    });
  }, [data, sortField, sortDirection]);

  const handleSort = (field: string) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  if (data.length === 0) {
    return (
      <div className="p-4 bg-white rounded-lg shadow">
        <p className="text-gray-500 text-center">No data available</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="p-4 border-b border-gray-200">
        <h3 className="text-lg font-bold">
          Data from {sourceName} ({data.length} records)
        </h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              {fields.map((field) => (
                <th
                  key={field}
                  onClick={() => handleSort(field)}
                  className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider cursor-pointer hover:bg-gray-100 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    {field.replace(/_/g, ' ')}
                    {sortField === field && (
                      <span className="text-blue-500">
                        {sortDirection === 'asc' ? '↑' : '↓'}
                      </span>
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {sortedData.map((row, idx) => (
              <tr key={idx} className="hover:bg-gray-50">
                {fields.map((field) => (
                  <td
                    key={field}
                    className="px-4 py-3 text-sm text-gray-900 font-mono"
                  >
                    {formatValue(row[field], field)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function formatValue(value: any, field: string): string {
  if (value === null || value === undefined) {
    return '-';
  }

  if (field === 'timestamp') {
    return new Date(value).toLocaleString();
  }

  if (typeof value === 'number') {
    return value.toLocaleString(undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  }

  return String(value);
}
