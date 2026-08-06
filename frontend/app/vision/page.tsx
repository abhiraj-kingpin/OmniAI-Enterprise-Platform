"use client";

import { useState } from "react";

import { API_BASE, apiGet, apiUpload } from "@/lib/backend";
import { Button, Card, FileInput, PageHeader, StatusLine, TextInput } from "@/components/ui";

interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

export default function VisionPage() {
  const [preview, setPreview] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [faces, setFaces] = useState<BoundingBox[] | null>(null);
  const [caption, setCaption] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);

  const [catalog, setCatalog] = useState("demo");
  const [catalogStatus, setCatalogStatus] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [matches, setMatches] = useState<{ filename: string; similarity: number }[]>([]);

  function onSelect(f: File) {
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setFaces(null);
    setCaption(null);
  }

  async function runFaces() {
    if (!file) return;
    setStatus("Detecting faces...");
    const form = new FormData();
    form.append("file", file);
    try {
      const res = await apiUpload<{ faces: BoundingBox[] }>("/api/vision/faces", form);
      setFaces(res.faces);
      setStatus(`Found ${res.faces.length} face(s).`);
    } catch (err) {
      setStatus(err instanceof Error ? err.message : "Failed");
    }
  }

  async function runCaption() {
    if (!file) return;
    setStatus("Captioning with Claude vision...");
    const form = new FormData();
    form.append("file", file);
    try {
      const res = await apiUpload<{ caption: string }>("/api/vision/caption", form);
      setCaption(res.caption);
      setStatus(null);
    } catch (err) {
      setStatus(err instanceof Error ? err.message : "Failed");
    }
  }

  async function indexToCatalog() {
    if (!file) return;
    setCatalogStatus("Indexing into catalog...");
    const form = new FormData();
    form.append("file", file);
    try {
      const res = await apiUpload<{ total_images: number }>(
        `/api/vision/catalog/${catalog}/index`,
        form,
      );
      setCatalogStatus(`Catalog "${catalog}" now has ${res.total_images} image(s).`);
    } catch (err) {
      setCatalogStatus(err instanceof Error ? err.message : "Failed");
    }
  }

  async function searchCatalog() {
    if (!searchQuery.trim()) return;
    const res = await apiGet<{ matches: { filename: string; similarity: number }[] }>(
      `/api/vision/catalog/${catalog}/search?query=${encodeURIComponent(searchQuery)}&top_k=5`,
    );
    setMatches(res.matches);
  }

  return (
    <div className="mx-auto max-w-3xl p-8">
      <PageHeader
        title="Computer Vision"
        description="Classical OpenCV (faces, edges), Claude vision (captioning, classification), and real CLIP-based product search."
      />

      <div className="space-y-4">
        <Card title="1. Upload an image">
          <FileInput label="Image (PNG/JPG)" accept="image/*" onSelect={onSelect} />
          {preview && (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={preview} alt="preview" className="mt-3 max-h-64 rounded-lg" />
          )}
          {file && (
            <div className="mt-3 flex flex-wrap gap-2">
              <Button onClick={runFaces} variant="secondary">
                Detect faces
              </Button>
              <Button onClick={runCaption} variant="secondary">
                Caption (Claude)
              </Button>
              <Button onClick={indexToCatalog} variant="secondary">
                Add to catalog
              </Button>
            </div>
          )}
          <div className="mt-2">
            <StatusLine text={status} />
          </div>
          {faces && <p className="mt-1 text-xs text-neutral-400">Faces: {JSON.stringify(faces)}</p>}
          {caption && <p className="mt-1 text-xs text-neutral-300">&ldquo;{caption}&rdquo;</p>}
        </Card>

        <Card title="2. CLIP product search">
          <div className="flex gap-2">
            <TextInput value={catalog} onChange={setCatalog} placeholder="catalog name" />
          </div>
          <div className="mt-2">
            <StatusLine text={catalogStatus} />
          </div>
          <div className="mt-3 flex gap-2">
            <TextInput value={searchQuery} onChange={setSearchQuery} placeholder="a photo of..." />
            <Button onClick={searchCatalog}>Search</Button>
          </div>
          <div className="mt-3 space-y-1">
            {matches.map((m, i) => (
              <p key={i} className="text-xs text-neutral-400">
                {m.filename} — similarity {m.similarity.toFixed(3)}
              </p>
            ))}
          </div>
        </Card>

        <p className="text-xs text-neutral-600">
          OCR endpoint (needs Tesseract installed):{" "}
          <code className="text-neutral-500">{API_BASE}/api/vision/ocr</code>
        </p>
      </div>
    </div>
  );
}
