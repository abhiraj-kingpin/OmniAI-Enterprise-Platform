"use client";

import { useState } from "react";

import { API_BASE, apiPost, apiUpload } from "@/lib/backend";
import { Button, Card, FileInput, PageHeader, StatusLine, TextArea } from "@/components/ui";

interface UploadResponse {
  dataset_id: string;
  rows: number;
  columns: { name: string; dtype: string }[];
}

interface SqlResponse {
  columns: string[];
  rows: unknown[][];
  row_count: number;
}

export default function DataAnalystPage() {
  const [dataset, setDataset] = useState<UploadResponse | null>(null);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);
  const [sql, setSql] = useState("SELECT * FROM dataset LIMIT 10");
  const [sqlResult, setSqlResult] = useState<SqlResponse | null>(null);
  const [chartUrl, setChartUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleUpload(file: File) {
    setUploadStatus(`Uploading ${file.name}...`);
    const form = new FormData();
    form.append("file", file);
    try {
      const res = await apiUpload<UploadResponse>("/api/data-analyst/upload", form);
      setDataset(res);
      setUploadStatus(`Loaded ${res.rows} rows, ${res.columns.length} columns.`);
    } catch (err) {
      setUploadStatus(err instanceof Error ? err.message : "Upload failed");
    }
  }

  async function runSql() {
    if (!dataset) return;
    setError(null);
    try {
      const res = await apiPost<SqlResponse>("/api/data-analyst/query", {
        dataset_id: dataset.dataset_id,
        sql,
      });
      setSqlResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Query failed");
    }
  }

  async function renderChart() {
    if (!dataset || dataset.columns.length === 0) return;
    const numeric = dataset.columns.find((c) => c.dtype.includes("int") || c.dtype.includes("float"));
    const categorical = dataset.columns.find((c) => !numeric || c.name !== numeric.name);
    if (!categorical) return;

    const res = await fetch(`${API_BASE}/api/data-analyst/chart`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        dataset_id: dataset.dataset_id,
        chart_type: "bar",
        x: categorical.name,
        y: numeric?.name,
        agg: "sum",
      }),
    });
    const blob = await res.blob();
    setChartUrl(URL.createObjectURL(blob));
  }

  return (
    <div className="mx-auto max-w-3xl p-8">
      <PageHeader
        title="AI Data Analyst"
        description="Upload a spreadsheet, query it with real SQL (DuckDB), auto-generate a chart, and get a Claude-written insights narrative."
      />

      <div className="space-y-4">
        <Card title="1. Upload">
          <FileInput label="CSV, XLSX, or JSON" accept=".csv,.xlsx,.xls,.json" onSelect={handleUpload} />
          <div className="mt-2">
            <StatusLine text={uploadStatus} />
          </div>
          {dataset && (
            <div className="mt-2 flex flex-wrap gap-1.5">
              {dataset.columns.map((c) => (
                <span key={c.name} className="rounded-full bg-neutral-800 px-2 py-0.5 text-[10px] text-neutral-400">
                  {c.name}: {c.dtype}
                </span>
              ))}
            </div>
          )}
        </Card>

        {dataset && (
          <>
            <Card title="2. Query with SQL">
              <TextArea value={sql} onChange={setSql} rows={3} />
              <div className="mt-2 flex gap-2">
                <Button onClick={runSql}>Run query</Button>
                <Button onClick={renderChart} variant="secondary">
                  Auto-chart
                </Button>
              </div>
              <div className="mt-2">
                <StatusLine text={error} error />
              </div>
              {sqlResult && (
                <div className="mt-3 overflow-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr>
                        {sqlResult.columns.map((c) => (
                          <th key={c} className="border-b border-neutral-800 p-1 text-left text-neutral-400">
                            {c}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {sqlResult.rows.map((row, i) => (
                        <tr key={i}>
                          {row.map((cell, j) => (
                            <td key={j} className="border-b border-neutral-900 p-1 text-neutral-300">
                              {String(cell)}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Card>

            {chartUrl && (
              <Card title="Chart">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={chartUrl} alt="Generated chart" className="rounded-lg" />
              </Card>
            )}

            <p className="text-xs text-neutral-600">
              Full dashboard (auto insights + suggested charts):{" "}
              <code className="text-neutral-400">
                GET /api/data-analyst/{dataset.dataset_id}/dashboard
              </code>
            </p>
          </>
        )}
      </div>
    </div>
  );
}
