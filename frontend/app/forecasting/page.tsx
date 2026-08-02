"use client";

import { useState } from "react";

import { apiPost, apiUpload } from "@/lib/backend";
import { Button, Card, FileInput, PageHeader, StatusLine, TextInput } from "@/components/ui";

interface UploadResponse {
  dataset_id: string;
  columns: { name: string }[];
}

interface ForecastPoint {
  date: string;
  forecast: number;
  lower: number | null;
  upper: number | null;
}

function Sparkline({ points }: { points: ForecastPoint[] }) {
  if (points.length === 0) return null;
  const values = points.map((p) => p.forecast);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const w = 400;
  const h = 100;
  const step = w / (points.length - 1 || 1);
  const path = points
    .map((p, i) => `${i === 0 ? "M" : "L"}${i * step},${h - ((p.forecast - min) / range) * h}`)
    .join(" ");
  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="w-full">
      <path d={path} fill="none" stroke="#3b82f6" strokeWidth={2} />
    </svg>
  );
}

export default function ForecastingPage() {
  const [dataset, setDataset] = useState<UploadResponse | null>(null);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);
  const [dateCol, setDateCol] = useState("date");
  const [valueCol, setValueCol] = useState("value");
  const [method, setMethod] = useState<"ets" | "arima">("ets");
  const [forecast, setForecast] = useState<ForecastPoint[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleUpload(file: File) {
    setUploadStatus(`Uploading ${file.name}...`);
    const form = new FormData();
    form.append("file", file);
    try {
      const res = await apiUpload<UploadResponse>("/api/data-analyst/upload", form);
      setDataset(res);
      setUploadStatus(`Loaded. Columns: ${res.columns.map((c) => c.name).join(", ")}`);
    } catch (err) {
      setUploadStatus(err instanceof Error ? err.message : "Upload failed");
    }
  }

  async function runForecast() {
    if (!dataset) return;
    setLoading(true);
    setError(null);
    try {
      const res = await apiPost<{ forecast: ForecastPoint[] }>("/api/forecasting/forecast", {
        dataset_id: dataset.dataset_id,
        date_col: dateCol,
        value_col: valueCol,
        horizon: 14,
        method,
      });
      setForecast(res.forecast);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Forecast failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl p-8">
      <PageHeader
        title="Forecasting"
        description="Upload a time series CSV (a date column + a numeric value column), pick a model, and forecast 14 periods ahead."
      />

      <div className="space-y-4">
        <Card title="1. Upload time series">
          <FileInput label="CSV with a date column and a value column" accept=".csv" onSelect={handleUpload} />
          <div className="mt-2">
            <StatusLine text={uploadStatus} />
          </div>
        </Card>

        {dataset && (
          <Card title="2. Configure and run">
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="mb-1 block text-xs text-neutral-500">Date column</label>
                <TextInput value={dateCol} onChange={setDateCol} />
              </div>
              <div>
                <label className="mb-1 block text-xs text-neutral-500">Value column</label>
                <TextInput value={valueCol} onChange={setValueCol} />
              </div>
            </div>
            <div className="mt-2 flex gap-2">
              <select
                value={method}
                onChange={(e) => setMethod(e.target.value as "ets" | "arima")}
                className="rounded-lg border border-neutral-700 bg-neutral-900 px-2 py-2 text-sm"
              >
                <option value="ets">ETS (Holt-Winters)</option>
                <option value="arima">ARIMA</option>
              </select>
              <Button onClick={runForecast} disabled={loading}>
                {loading ? "Forecasting..." : "Run forecast"}
              </Button>
            </div>
            <div className="mt-2">
              <StatusLine text={error} error />
            </div>

            {forecast && (
              <div className="mt-4">
                <Sparkline points={forecast} />
                <div className="mt-2 overflow-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="text-neutral-500">
                        <th className="text-left">Date</th>
                        <th className="text-right">Forecast</th>
                        <th className="text-right">Range</th>
                      </tr>
                    </thead>
                    <tbody>
                      {forecast.map((p) => (
                        <tr key={p.date}>
                          <td className="text-neutral-300">{p.date}</td>
                          <td className="text-right text-neutral-300">{p.forecast.toFixed(2)}</td>
                          <td className="text-right text-neutral-500">
                            {p.lower?.toFixed(1)} – {p.upper?.toFixed(1)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </Card>
        )}
      </div>
    </div>
  );
}
