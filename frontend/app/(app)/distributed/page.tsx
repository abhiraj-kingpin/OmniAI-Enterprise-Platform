"use client";

import { useEffect, useState } from "react";

import { apiGet, apiPost } from "@/lib/backend";
import { Button, Card, PageHeader, StatusLine, TextArea } from "@/components/ui";

interface ComponentStatus {
  component: string;
  available: boolean;
  detail: string;
}

interface ParallelMapResult {
  results: { text_preview: string; word_count: number }[];
  wall_time_seconds: number;
  workers_used: number;
}

export default function DistributedPage() {
  const [components, setComponents] = useState<ComponentStatus[]>([]);
  const [items, setItems] = useState("the quick brown fox\njumps over the lazy dog\nray runs this in parallel");
  const [rayResult, setRayResult] = useState<ParallelMapResult | null>(null);
  const [status, setStatus] = useState<string | null>(null);

  useEffect(() => {
    apiGet<ComponentStatus[]>("/api/distributed/components").then(setComponents).catch(() => {});
  }, []);

  async function runRay() {
    setStatus("Running on local Ray cluster...");
    try {
      const res = await apiPost<ParallelMapResult>("/api/distributed/ray/parallel-map", {
        items: items.split("\n").filter((l) => l.trim()),
      });
      setRayResult(res);
      setStatus(null);
    } catch (err) {
      setStatus(err instanceof Error ? err.message : "Failed");
    }
  }

  return (
    <div className="mx-auto max-w-3xl p-8">
      <PageHeader
        title="Distributed AI Infrastructure"
        description="Live, honest status for Ray, Celery/Redis, Kafka, Spark, ONNX Runtime, and vLLM/TensorRT-LLM — plus a real distributed computation running on a local Ray cluster."
      />

      <div className="space-y-4">
        <Card title="Component status (live check)">
          <div className="space-y-1.5">
            {components.map((c) => (
              <div key={c.component} className="rounded-lg border border-neutral-800 p-2 text-xs">
                <p className="flex items-center gap-2">
                  <span className={`h-1.5 w-1.5 rounded-full ${c.available ? "bg-green-500" : "bg-neutral-600"}`} />
                  <span className="font-medium text-neutral-200">{c.component}</span>
                </p>
                <p className="mt-1 text-neutral-500">{c.detail}</p>
              </div>
            ))}
          </div>
        </Card>

        <Card title="Ray: parallel-map demo (genuinely distributed)">
          <TextArea value={items} onChange={setItems} rows={3} />
          <div className="mt-2">
            <Button onClick={runRay}>Run on Ray cluster</Button>
          </div>
          <div className="mt-2">
            <StatusLine text={status} />
          </div>
          {rayResult && (
            <div className="mt-3 space-y-1">
              <p className="text-xs text-neutral-500">
                {rayResult.wall_time_seconds}s wall time · {rayResult.workers_used} worker(s)
              </p>
              {rayResult.results.map((r, i) => (
                <p key={i} className="text-xs text-neutral-300">
                  &ldquo;{r.text_preview}&rdquo; — {r.word_count} words
                </p>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
