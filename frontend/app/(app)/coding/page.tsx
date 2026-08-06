"use client";

import { useState } from "react";

import { apiPost } from "@/lib/backend";
import { Button, Card, PageHeader, StatusLine, TextInput } from "@/components/ui";

interface GenerateResponse {
  code: string;
  explanation: string;
}

interface SearchResult {
  source: string;
  text: string;
  score: number;
}

export default function CodingPage() {
  const [prompt, setPrompt] = useState("A function that merges two sorted lists");
  const [generated, setGenerated] = useState<GenerateResponse | null>(null);
  const [genLoading, setGenLoading] = useState(false);

  const [owner, setOwner] = useState("pallets");
  const [repo, setRepo] = useState("flask");
  const [indexStatus, setIndexStatus] = useState<string | null>(null);
  const [collection, setCollection] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);

  async function generate() {
    setGenLoading(true);
    try {
      const res = await apiPost<GenerateResponse>("/api/coding/generate", { prompt, language: "python" });
      setGenerated(res);
    } catch (err) {
      setGenerated({ code: "", explanation: err instanceof Error ? err.message : "Failed" });
    } finally {
      setGenLoading(false);
    }
  }

  async function indexRepo() {
    setIndexStatus(`Indexing ${owner}/${repo}...`);
    try {
      const res = await apiPost<{ collection: string; files_indexed: number; chunks_indexed: number }>(
        "/api/coding/github/index",
        { owner, repo, max_files: 15 },
      );
      setCollection(res.collection);
      setIndexStatus(`Indexed ${res.files_indexed} files, ${res.chunks_indexed} chunks.`);
    } catch (err) {
      setIndexStatus(err instanceof Error ? err.message : "Indexing failed");
    }
  }

  async function searchRepo() {
    if (!collection || !searchQuery.trim()) return;
    const res = await apiPost<{ results: SearchResult[] }>("/api/coding/search", {
      collection,
      query: searchQuery,
      top_k: 5,
    });
    setResults(res.results);
  }

  return (
    <div className="mx-auto max-w-3xl p-8">
      <PageHeader
        title="AI Coding Assistant"
        description="Generate code, or index a real GitHub repo's Python files and search them semantically."
      />

      <div className="space-y-4">
        <Card title="Code generation">
          <TextInput value={prompt} onChange={setPrompt} />
          <div className="mt-2">
            <Button onClick={generate} disabled={genLoading}>
              {genLoading ? "Generating..." : "Generate"}
            </Button>
          </div>
          {generated && (
            <div className="mt-3 space-y-2">
              <pre className="overflow-auto rounded-lg bg-neutral-950 p-3 text-xs text-neutral-200">
                {generated.code}
              </pre>
              <p className="text-xs text-neutral-500">{generated.explanation}</p>
            </div>
          )}
        </Card>

        <Card title="GitHub repository search">
          <div className="flex gap-2">
            <TextInput value={owner} onChange={setOwner} placeholder="owner" />
            <TextInput value={repo} onChange={setRepo} placeholder="repo" />
            <Button onClick={indexRepo} variant="secondary">
              Index
            </Button>
          </div>
          <div className="mt-2">
            <StatusLine text={indexStatus} />
          </div>

          {collection && (
            <div className="mt-3 flex gap-2">
              <TextInput value={searchQuery} onChange={setSearchQuery} placeholder="How does routing work?" />
              <Button onClick={searchRepo}>Search</Button>
            </div>
          )}

          <div className="mt-3 space-y-2">
            {results.map((r, i) => (
              <div key={i} className="rounded-lg border border-neutral-800 p-2 text-xs">
                <p className="mb-1 text-neutral-500">{r.source} · score {r.score.toFixed(2)}</p>
                <pre className="overflow-auto text-neutral-400">{r.text.slice(0, 300)}</pre>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
