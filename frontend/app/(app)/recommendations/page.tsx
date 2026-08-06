"use client";

import { useState } from "react";

import { apiGet, apiPost } from "@/lib/backend";
import { Button, Card, PageHeader, StatusLine, TextInput } from "@/components/ui";

interface UploadResponse {
  dataset_id: string;
  users: number;
  items: number;
  interactions: number;
}

interface RecommendationItem {
  item_id: string;
  predicted_rating: number;
  final_score: number;
}

export default function RecommendationsPage() {
  const [dataset, setDataset] = useState<UploadResponse | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [userId, setUserId] = useState("user_0");
  const [recs, setRecs] = useState<RecommendationItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function loadDemo() {
    setBusy(true);
    setStatus("Generating demo interactions...");
    try {
      const res = await apiPost<UploadResponse>("/api/recommendations/demo-dataset");
      setDataset(res);
      setStatus(`${res.users} users, ${res.items} items, ${res.interactions} interactions. Training...`);
      const train = await apiPost<{ final_rmse: number }>("/api/recommendations/train", {
        dataset_id: res.dataset_id,
        factors: 10,
        epochs: 25,
      });
      setStatus(`Trained — final RMSE ${train.final_rmse.toFixed(3)}.`);
    } catch (err) {
      setStatus(err instanceof Error ? err.message : "Failed");
    } finally {
      setBusy(false);
    }
  }

  async function getRecommendations() {
    if (!dataset) return;
    setError(null);
    try {
      const res = await apiGet<{ recommendations: RecommendationItem[] }>(
        `/api/recommendations/${dataset.dataset_id}/recommend/${userId}?top_k=8`,
      );
      setRecs(res.recommendations);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to get recommendations");
    }
  }

  return (
    <div className="mx-auto max-w-3xl p-8">
      <PageHeader
        title="Recommendation System"
        description="Matrix factorization collaborative filtering, trained live. Generates a synthetic dataset so you can try it with no upload."
      />

      <div className="space-y-4">
        <Card title="1. Generate + train">
          <Button onClick={loadDemo} disabled={busy}>
            {busy ? "Working..." : "Generate demo data and train"}
          </Button>
          <div className="mt-2">
            <StatusLine text={status} />
          </div>
        </Card>

        {dataset && (
          <Card title="2. Get recommendations">
            <div className="flex gap-2">
              <TextInput value={userId} onChange={setUserId} placeholder="user_0" />
              <Button onClick={getRecommendations}>Recommend</Button>
            </div>
            <div className="mt-2">
              <StatusLine text={error} error />
            </div>
            {recs && (
              <div className="mt-3 space-y-1.5">
                {recs.map((r) => (
                  <div key={r.item_id} className="flex justify-between rounded-lg border border-neutral-800 px-3 py-1.5 text-xs">
                    <span className="text-neutral-300">{r.item_id}</span>
                    <span className="text-neutral-500">
                      predicted {r.predicted_rating.toFixed(2)} · score {r.final_score.toFixed(2)}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </Card>
        )}
      </div>
    </div>
  );
}
