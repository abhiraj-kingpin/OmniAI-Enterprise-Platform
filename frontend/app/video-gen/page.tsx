"use client";

import { useEffect, useState } from "react";

import { API_BASE, apiGet } from "@/lib/backend";
import { Button, Card, FileInput, PageHeader, StatusLine } from "@/components/ui";

interface Availability {
  available: string;
  reason?: string;
}

export default function VideoGenPage() {
  const [frameA, setFrameA] = useState<File | null>(null);
  const [frameB, setFrameB] = useState<File | null>(null);
  const [gifUrl, setGifUrl] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [availability, setAvailability] = useState<Availability | null>(null);

  useEffect(() => {
    apiGet<Availability>("/api/video-gen/availability").then(setAvailability).catch(() => {});
  }, []);

  async function interpolate() {
    if (!frameA || !frameB) return;
    setStatus("Running optical-flow interpolation...");
    const form = new FormData();
    form.append("frame_a", frameA);
    form.append("frame_b", frameB);
    form.append("n_intermediate", "8");
    form.append("format", "gif");

    try {
      const res = await fetch(`${API_BASE}/api/video-gen/interpolate`, { method: "POST", body: form });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      const download = await fetch(
        `${API_BASE}/api/video-gen/interpolate/download?path=${encodeURIComponent(data.output_path)}`,
      );
      const blob = await download.blob();
      setGifUrl(URL.createObjectURL(blob));
      setStatus(`Generated ${data.frames_generated} frames.`);
    } catch (err) {
      setStatus(err instanceof Error ? err.message : "Failed");
    }
  }

  return (
    <div className="mx-auto max-w-3xl p-8">
      <PageHeader
        title="AI Video Generator"
        description="Real, running frame interpolation via classical optical flow — upload two frames, get the in-between motion. Text-to-video diffusion is also implemented; see the availability note below."
      />

      <div className="space-y-4">
        <Card title="Frame interpolation (runs for real)">
          <div className="grid grid-cols-2 gap-2">
            <FileInput label="Frame A" accept="image/*" onSelect={setFrameA} />
            <FileInput label="Frame B" accept="image/*" onSelect={setFrameB} />
          </div>
          <div className="mt-2">
            <Button onClick={interpolate} disabled={!frameA || !frameB}>
              Interpolate
            </Button>
          </div>
          <div className="mt-2">
            <StatusLine text={status} />
          </div>
          {gifUrl && (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={gifUrl} alt="Interpolated animation" className="mt-3 rounded-lg" />
          )}
        </Card>

        <Card title="Text-to-video diffusion — availability">
          {availability ? (
            availability.available === "true" ? (
              <p className="text-sm text-green-400">Available on this host.</p>
            ) : (
              <StatusLine text={availability.reason ?? "Unavailable"} error />
            )
          ) : (
            <StatusLine text="Checking..." />
          )}
        </Card>
      </div>
    </div>
  );
}
