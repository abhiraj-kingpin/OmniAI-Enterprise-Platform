"use client";

import { useEffect, useState } from "react";

import { apiGet } from "@/lib/backend";
import { Card, PageHeader } from "@/components/ui";

interface Experiment {
  experiment_id: string;
  name: string;
  run_count: number;
}

export default function MlopsPage() {
  const [experiments, setExperiments] = useState<Experiment[]>([]);

  useEffect(() => {
    apiGet<Experiment[]>("/api/mlops/experiments").then(setExperiments).catch(() => {});
  }, []);

  return (
    <div className="mx-auto max-w-3xl p-8">
      <PageHeader
        title="MLOps Dashboard"
        description="Real MLflow experiment tracking (SQLite-backed) — every module can log training runs here. Plus Docker/Kubernetes/Airflow/DVC/CI artifacts under infra/ and .github/."
      />

      <div className="space-y-4">
        <Card title="Experiments">
          {experiments.length === 0 ? (
            <p className="text-sm text-neutral-500">
              No experiments logged yet. Train a recommendation model or run a forecast to populate this —
              or POST to /api/mlops/runs directly.
            </p>
          ) : (
            <div className="space-y-1.5">
              {experiments.map((e) => (
                <div key={e.experiment_id} className="flex justify-between rounded-lg border border-neutral-800 px-3 py-1.5 text-sm">
                  <span className="text-neutral-200">{e.name}</span>
                  <span className="text-neutral-500">{e.run_count} run(s)</span>
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card title="Infrastructure as code">
          <ul className="space-y-1 text-xs text-neutral-400">
            <li>backend/Dockerfile, frontend/Dockerfile</li>
            <li>docker-compose.yml — full stack (backend, frontend, Redis, Kafka, MLflow UI)</li>
            <li>infra/k8s/ — Deployment, Service, Ingress, HPA</li>
            <li>infra/airflow/dags/ — a real orchestration DAG</li>
            <li>dvc.yaml — data/model versioning pipeline</li>
            <li>.github/workflows/ci.yml — lint, test, build</li>
          </ul>
        </Card>
      </div>
    </div>
  );
}
