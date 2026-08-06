"use client";

import { useEffect, useState } from "react";

import { apiGet } from "@/lib/backend";
import { AvailabilityCard, Card, PageHeader } from "@/components/ui";
import type { Availability } from "@/lib/types";

interface RlhfConcepts {
  summary: string;
  stages: { stage: string; description: string }[];
  why_not_implemented_here: string;
}

export default function FinetunePage() {
  const [availability, setAvailability] = useState<Availability | null>(null);
  const [rlhf, setRlhf] = useState<RlhfConcepts | null>(null);

  useEffect(() => {
    apiGet<Availability>("/api/finetune/availability").then(setAvailability).catch(() => {});
    apiGet<RlhfConcepts>("/api/finetune/rlhf-concepts").then(setRlhf).catch(() => {});
  }, []);

  return (
    <div className="mx-auto max-w-3xl p-8">
      <PageHeader
        title="Fine-Tuning"
        description="A real LoRA fine-tuning pipeline (PEFT + Transformers) — job submission, background training, before/after eval loss."
      />

      <div className="space-y-4">
        <Card title="Availability">
          <AvailabilityCard
            availability={availability}
            availableMessage="Available — POST /api/finetune/jobs to start a training run."
          />
        </Card>

        {rlhf && (
          <Card title="RLHF (concepts)">
            <p className="mb-3 text-sm text-neutral-300">{rlhf.summary}</p>
            <div className="space-y-2">
              {rlhf.stages.map((s) => (
                <div key={s.stage} className="rounded-lg border border-neutral-800 p-2 text-xs">
                  <p className="font-medium text-neutral-200">{s.stage}</p>
                  <p className="mt-0.5 text-neutral-500">{s.description}</p>
                </div>
              ))}
            </div>
            <p className="mt-3 text-xs text-neutral-600">{rlhf.why_not_implemented_here}</p>
          </Card>
        )}
      </div>
    </div>
  );
}
