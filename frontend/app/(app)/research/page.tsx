"use client";

import { useState } from "react";

import { apiPost } from "@/lib/backend";
import { Button, Card, PageHeader, StatusLine, TextInput } from "@/components/ui";

interface Paper {
  arxiv_id: string;
  title: string;
  authors: string[];
  abstract: string;
}

export default function ResearchPage() {
  const [query, setQuery] = useState("");
  const [papers, setPapers] = useState<Paper[]>([]);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<string | null>(null);
  const [consulted, setConsulted] = useState<Paper[]>([]);
  const [loading, setLoading] = useState<"search" | "assistant" | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function search() {
    if (!query.trim()) return;
    setLoading("search");
    setError(null);
    try {
      const res = await apiPost<{ papers: Paper[] }>("/api/research/search", {
        query,
        max_results: 5,
      });
      setPapers(res.papers);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setLoading(null);
    }
  }

  async function askAssistant() {
    if (!question.trim()) return;
    setLoading("assistant");
    setError(null);
    setAnswer(null);
    try {
      const res = await apiPost<{ answer: string; papers_consulted: Paper[] }>(
        "/api/research/assistant",
        { question, max_searches: 3 },
      );
      setAnswer(res.answer);
      setConsulted(res.papers_consulted);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Assistant failed");
    } finally {
      setLoading(null);
    }
  }

  return (
    <div className="mx-auto max-w-3xl p-8">
      <PageHeader
        title="AI Research Assistant"
        description="Search arXiv directly, or ask the research agent a question — it searches arXiv on its own, as many times as it needs, and answers with citations."
      />

      <div className="space-y-4">
        <Card title="Search arXiv">
          <div className="flex gap-2">
            <TextInput value={query} onChange={setQuery} placeholder="retrieval augmented generation" />
            <Button onClick={search} disabled={loading === "search"}>
              {loading === "search" ? "Searching..." : "Search"}
            </Button>
          </div>
          <div className="mt-3 space-y-2">
            {papers.map((p) => (
              <div key={p.arxiv_id} className="rounded-lg border border-neutral-800 p-2 text-xs">
                <p className="font-medium text-neutral-200">{p.title}</p>
                <p className="mt-0.5 text-neutral-500">{p.authors.join(", ")} · {p.arxiv_id}</p>
                <p className="mt-1 text-neutral-400">{p.abstract.slice(0, 220)}...</p>
              </div>
            ))}
          </div>
        </Card>

        <Card title="Ask the research agent">
          <div className="flex gap-2">
            <TextInput
              value={question}
              onChange={setQuestion}
              placeholder="What are the leading approaches to hybrid retrieval?"
            />
            <Button onClick={askAssistant} disabled={loading === "assistant"}>
              {loading === "assistant" ? "Researching..." : "Ask"}
            </Button>
          </div>
          <div className="mt-2">
            <StatusLine text={error} error />
          </div>
          {answer && (
            <div className="mt-3 space-y-3">
              <div className="rounded-lg bg-neutral-950 p-3 text-sm text-neutral-200">{answer}</div>
              <div className="space-y-1">
                {consulted.map((p) => (
                  <p key={p.arxiv_id} className="text-xs text-neutral-500">
                    [{p.arxiv_id}] {p.title}
                  </p>
                ))}
              </div>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
