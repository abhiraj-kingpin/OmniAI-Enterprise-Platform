"use client";

import { useEffect, useState } from "react";

import { apiGet, apiPost } from "@/lib/backend";
import { AvailabilityCard, Button, Card, PageHeader, StatusLine, TextInput } from "@/components/ui";
import type { Availability } from "@/lib/types";

export default function ImageGenPage() {
  const [availability, setAvailability] = useState<Availability | null>(null);
  const [prompt, setPrompt] = useState("a watercolor painting of a lighthouse at sunset");
  const [jobStatus, setJobStatus] = useState<string | null>(null);

  useEffect(() => {
    apiGet<Availability>("/api/image-gen/availability").then(setAvailability).catch(() => {});
  }, []);

  async function generate() {
    setJobStatus("Submitting job...");
    try {
      const res = await apiPost<{ status: string; error?: string }>("/api/image-gen/generate", {
        prompt,
        width: 512,
        height: 512,
        steps: 25,
      });
      setJobStatus(res.error ? `Failed: ${res.error}` : `Job status: ${res.status}`);
    } catch (err) {
      setJobStatus(err instanceof Error ? err.message : "Failed");
    }
  }

  return (
    <div className="mx-auto max-w-3xl p-8">
      <PageHeader
        title="AI Image Generator"
        description="A real Stable Diffusion pipeline (diffusers): text-to-image, LoRA adapters, inpainting, and ControlNet — see backend/app/modules/image_gen/pipeline.py."
      />

      <div className="space-y-4">
        <Card title="Availability">
          <AvailabilityCard availability={availability} availableMessage="Available for generation." />
        </Card>

        <Card title="Generate">
          <TextInput value={prompt} onChange={setPrompt} />
          <div className="mt-2">
            <Button onClick={generate}>Submit generation job</Button>
          </div>
          <div className="mt-2">
            <StatusLine text={jobStatus} />
          </div>
        </Card>
      </div>
    </div>
  );
}
