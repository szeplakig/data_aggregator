// Generic data table component
import { useState, useMemo } from "react";
import type { DataPoint } from "../types/api";

interface FieldMeta {
  unit?: string;
  format?: string;
  display_name?: string;
  [key: string]: any;
}

interface DataTableProps {
  data: DataPoint[];
  sourceName: string;
  field_metadata?: Record<string, FieldMeta>;
}

export function DataTable({ data, sourceName, field_metadata }: DataTableProps) {
  const [sortField, setSortField] = useState<string>("timestamp");
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("desc");

  // Extract all field names dynamically
  const fields = useMemo(() => {
    if (data.length === 0) return [];

    const allFields = new Set<string>();
    data.forEach((row) => {
      Object.keys(row).forEach((key) => allFields.add(key));
    });
    // Put timestamp first
    const fieldArray = Array.from(allFields);
    return ["timestamp", ...fieldArray.filter((f) => f !== "timestamp")];
  }, [data]);

  // Sort data
  const sortedData = useMemo(() => {
    return [...data].sort((a, b) => {
      const aVal = a[sortField];
      const bVal = b[sortField];

      if (aVal === null || aVal === undefined) return 1;
      if (bVal === null || bVal === undefined) return -1;

      let comparison = 0;
      if (typeof aVal === "string" && typeof bVal === "string") {
        comparison = aVal.localeCompare(bVal);
      } else {
        comparison = aVal > bVal ? 1 : aVal < bVal ? -1 : 0;
      }

      return sortDirection === "asc" ? comparison : -comparison;
    });
  }, [data, sortField, sortDirection]);

  const handleSort = (field: string) => {
    if (sortField === field) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDirection("asc");
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
                    {(field_metadata?.[field]?.display_name) ?? field.replace(/_/g, " ")}
                    {sortField === field && (
                      <span className="text-blue-500">
                        {sortDirection === "asc" ? "↑" : "↓"}
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
                    {formatValue(row[field], field, field_metadata?.[field])}
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

function formatValue(value: any, field: string, meta?: FieldMeta): string {
  if (value === null || value === undefined) {
    return "-";
  }

  if (field === "timestamp") {
    const d = new Date(value);
    if (isNaN(d.getTime())) return "-";
    return d.toLocaleString();
  }

  if (typeof value === "number") {
    // Determine decimals from meta.format if provided (supports python-like '{:.2f}')
    // Force integer for 'count' fields
    let decimals = field === 'count' ? 0 : 2;
    if (field !== 'count' && meta?.format) {
      const m = meta.format.match(/\{:\.(\d+)f\}/);
      if (m) decimals = parseInt(m[1], 10);
    }

    const formatted = value.toLocaleString(undefined, {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    });

    const unit = meta?.unit ? ` ${meta.unit}` : '';
    return formatted + unit;
  }

  return String(value);
}
