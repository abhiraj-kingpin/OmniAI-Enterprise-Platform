"use client";

import { useState } from "react";

import { apiFileUrl, apiPost, apiUpload } from "@/lib/backend";
import { Button, Card, FileInput, PageHeader, StatusLine, TextInput } from "@/components/ui";

interface RetrievedChunk {
  chunk: { text: string; source: string };
  fused_score: number;
  rerank_score: number | null;
}

interface QueryResponse {
  answer: string | null;
  retrieved: RetrievedChunk[];
}

export default function RagPage() {
  const [collection, setCollection] = useState("default");
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleUpload(file: File) {
    setUploadStatus(`Uploading ${file.name}...`);
    const form = new FormData();
    form.append("file", file);
    form.append("collection", collection);
    try {
      const res = await apiUpload<{ chunks_indexed: number }>("/api/rag/upload", form);
      setUploadStatus(`Indexed ${res.chunks_indexed} chunks from ${file.name}.`);
    } catch (err) {
      setUploadStatus(err instanceof Error ? err.message : "Upload failed");
    }
  }

  async function handleQuery() {
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await apiPost<QueryResponse>("/api/rag/query", {
        collection,
        query,
        top_k: 5,
        rerank: true,
        answer: true,
      });
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Query failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl p-8">
      <PageHeader
        title="Enterprise RAG"
        description="Upload documents, then ask questions — hybrid BM25 + ONNX embedding search, cross-encoder reranked, answered with citations."
      />

      <div className="space-y-4">
        <Card title="1. Collection">
          <TextInput value={collection} onChange={setCollection} placeholder="Collection name" />
        </Card>

        <Card title="2. Upload a document">
          <FileInput
            label="PDF, DOCX, XLSX, PPTX, TXT, or an image (OCR)"
            accept=".pdf,.docx,.xlsx,.pptx,.txt,.md,.png,.jpg,.jpeg"
            onSelect={handleUpload}
          />
          <div className="mt-2">
            <StatusLine text={uploadStatus} />
          </div>
        </Card>

        <Card title="3. Ask a question">
          <div className="flex gap-2">
            <TextInput value={query} onChange={setQuery} placeholder="What does the document say about...?" />
            <Button onClick={handleQuery} disabled={loading}>
              {loading ? "Searching..." : "Ask"}
            </Button>
          </div>
          <div className="mt-2">
            <StatusLine text={error} error />
          </div>

          {result && (
            <div className="mt-4 space-y-3">
              {result.answer && (
                <div className="rounded-lg bg-neutral-950 p-3 text-sm text-neutral-200">
                  {result.answer}
                </div>
              )}
              <div className="space-y-2">
                {result.retrieved.map((r, i) => (
                  <div key={i} className="rounded-lg border border-neutral-800 p-2 text-xs">
                    <p className="mb-1 text-neutral-500">
                      {r.chunk.source} · score {(r.rerank_score ?? r.fused_score).toFixed(3)}
                    </p>
                    <p className="text-neutral-400">{r.chunk.text.slice(0, 200)}...</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </Card>

        <p className="text-xs text-neutral-600">
          Knowledge graph view:{" "}
          <a
            className="underline hover:text-neutral-400"
            href={apiFileUrl(`/api/rag/collections/${collection}/graph`)}
            target="_blank"
            rel="noreferrer"
          >
            /api/rag/collections/{collection}/graph
          </a>
        </p>
      </div>
    </div>
  );
}
