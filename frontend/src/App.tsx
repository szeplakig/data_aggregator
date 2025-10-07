import { useState } from "react";
import {
  QueryClient,
  QueryClientProvider,
  useQuery,
} from "@tanstack/react-query";
import { api } from "./api/client";
import { SourceSelector } from "./components/SourceSelector";
import { DataTable } from "./components/DataTable";
import { AggregatesPanel } from "./components/AggregatesPanel";
import "./App.css";

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function DataAggregatorApp() {
  const [selectedSource, setSelectedSource] = useState<string | null>(null);
  const [dataLimit, setDataLimit] = useState<number>(100);
  const [hoursFilter, setHoursFilter] = useState<number | null>(24);

  // Fetch sources
  const {
    data: sources = [],
    isLoading: sourcesLoading,
    error: sourcesError,
  } = useQuery({
    queryKey: ["sources"],
    queryFn: () => api.getSources(true),
  });

  // Fetch data for selected source
  const {
    data: dataResponse,
    isLoading: dataLoading,
    error: dataError,
    refetch: refetchData,
  } = useQuery({
    queryKey: ["data", selectedSource, dataLimit, hoursFilter],
    queryFn: () =>
      api.getData(selectedSource!, {
        limit: dataLimit,
        hours: hoursFilter || undefined,
      }),
    enabled: !!selectedSource,
  });

  const handleRefresh = async () => {
    if (selectedSource) {
      try {
        await api.triggerFetch(selectedSource);
        // Wait a bit for the fetch to complete, then refetch data
        setTimeout(() => {
          refetchData();
        }, 2000);
      } catch (error) {
        console.error("Failed to trigger fetch:", error);
      }
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold text-gray-900">
            Data Aggregator Dashboard
          </h1>
          <p className="text-gray-600 mt-1">
            Generic data aggregation from multiple sources
          </p>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        <div className="space-y-6">
          {/* Error messages */}
          {sourcesError && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
              Error loading sources: {(sourcesError as Error).message}
            </div>
          )}

          {/* Source selector */}
          <SourceSelector
            sources={sources}
            selectedSource={selectedSource}
            onSourceSelect={setSelectedSource}
            isLoading={sourcesLoading}
          />

          {/* Data view */}
          {selectedSource && (
            <>
              {/* Controls */}
              <div className="p-4 bg-white rounded-lg shadow flex flex-wrap gap-4 items-center">
                <div className="flex items-center gap-2">
                  <label className="text-sm font-medium text-gray-700">
                    Show last:
                  </label>
                  <select
                    value={hoursFilter || ""}
                    onChange={(e) =>
                      setHoursFilter(
                        e.target.value ? parseInt(e.target.value) : null
                      )
                    }
                    className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">All time</option>
                    <option value="1">1 hour</option>
                    <option value="6">6 hours</option>
                    <option value="24">24 hours</option>
                    <option value="168">7 days</option>
                  </select>
                </div>

                <div className="flex items-center gap-2">
                  <label className="text-sm font-medium text-gray-700">
                    Limit:
                  </label>
                  <input
                    type="number"
                    value={dataLimit}
                    onChange={(e) =>
                      setDataLimit(Math.max(1, parseInt(e.target.value) || 1))
                    }
                    className="w-24 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    min="1"
                    max="10000"
                  />
                </div>

                <button
                  onClick={handleRefresh}
                  disabled={dataLoading}
                  className="ml-auto px-4 py-2 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                >
                  {dataLoading ? "Loading..." : "Refresh Data"}
                </button>
              </div>

              {/* Error message */}
              {dataError && (
                <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
                  Error loading data: {(dataError as Error).message}
                </div>
              )}

              {/* Loading state */}
              {dataLoading && (
                <div className="p-8 bg-white rounded-lg shadow text-center">
                  <div className="inline-block animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full"></div>
                  <p className="mt-4 text-gray-600">Loading data...</p>
                </div>
              )}

              {/* Data display */}
              {dataResponse && !dataLoading && (
                <>
                  {/* Summary */}
                  <div className="p-4 bg-white rounded-lg shadow">
                    <div className="flex flex-wrap gap-4 text-sm">
                      <div>
                        <span className="text-gray-600">Source:</span>{" "}
                        <span className="font-medium">
                          {dataResponse.source}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-600">Type:</span>{" "}
                        <span className="font-medium">{dataResponse.type}</span>
                      </div>
                      <div>
                        <span className="text-gray-600">Total records:</span>{" "}
                        <span className="font-medium">
                          {dataResponse.total_count}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-600">Showing:</span>{" "}
                        <span className="font-medium">
                          {dataResponse.returned_count}
                        </span>
                      </div>
                      {dataResponse.period.from && (
                        <div>
                          <span className="text-gray-600">Period:</span>{" "}
                          <span className="font-medium">
                            {new Date(
                              dataResponse.period.from
                            ).toLocaleString()}{" "}
                            -{" "}
                            {dataResponse.period.to
                              ? new Date(
                                  dataResponse.period.to
                                ).toLocaleString()
                              : "-"}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Aggregates */}
                  <AggregatesPanel
                    aggregates={dataResponse.aggregates}
                    field_metadata={dataResponse.field_metadata}
                  />

                  {/* Data table */}
                  <DataTable
                    data={dataResponse.data}
                    sourceName={dataResponse.source}
                    field_metadata={dataResponse.field_metadata}
                  />
                </>
              )}
            </>
          )}

          {/* No source selected message */}
          {!selectedSource && !sourcesLoading && (
            <div className="p-8 bg-white rounded-lg shadow text-center text-gray-500">
              <p className="text-lg">
                Select a data source above to view its data
              </p>
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="mt-12 py-6 text-center text-gray-600 text-sm">
        <p>Generic Data Aggregator - Architecture II: Normal App</p>
      </footer>
    </div>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <DataAggregatorApp />
    </QueryClientProvider>
  );
}

export default App;
