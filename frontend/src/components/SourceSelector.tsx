// Source selector component
import type { Source } from '../types/api';

interface SourceSelectorProps {
  sources: Source[];
  selectedSource: string | null;
  onSourceSelect: (sourceName: string) => void;
  isLoading?: boolean;
}

export function SourceSelector({
  sources,
  selectedSource,
  onSourceSelect,
  isLoading = false,
}: SourceSelectorProps) {
  if (isLoading) {
    return (
      <div className="flex items-center gap-2 p-4 bg-white rounded-lg shadow">
        <div className="animate-spin h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full"></div>
        <span>Loading sources...</span>
      </div>
    );
  }

  return (
    <div className="p-4 bg-white rounded-lg shadow">
      <h2 className="text-xl font-bold mb-4">Data Sources</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {sources.map((source) => (
          <button
            key={source.id}
            onClick={() => onSourceSelect(source.name)}
            className={`p-4 rounded-lg border-2 transition-all text-left ${
              selectedSource === source.name
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50'
            } ${!source.enabled ? 'opacity-50 cursor-not-allowed' : ''}`}
            disabled={!source.enabled}
          >
            <div className="font-semibold text-lg">{source.name}</div>
            <div className="text-sm text-gray-600 mt-1">{source.type}</div>
            {source.meta?.location && (
              <div className="text-xs text-blue-600 mt-1 flex items-center gap-1">
                <span>📍</span>
                <span>{source.meta.location}</span>
              </div>
            )}
            {source.description && (
              <div className="text-xs text-gray-500 mt-2">
                {source.description}
              </div>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}
