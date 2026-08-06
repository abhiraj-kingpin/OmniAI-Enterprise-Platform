"use client";

import { useState } from "react";

import { apiPost } from "@/lib/backend";
import { Button, Card, PageHeader, StatusLine, TextInput } from "@/components/ui";

interface AgentAction {
  tool: string;
  input: Record<string, unknown>;
  result: string;
}

interface RunResponse {
  answer: string;
  actions: AgentAction[];
  status: string;
}

export default function BrowserAgentPage() {
  const [task, setTask] = useState("Go to https://www.wikipedia.org and tell me the page title");
  const [result, setResult] = useState<RunResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await apiPost<RunResponse>("/api/browser-agent/run", {
        task,
        max_steps: 10,
        headless: true,
      });
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Run failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl p-8">
      <PageHeader
        title="Autonomous Browser Agent"
        description="Claude plans and drives a real headless Chromium browser (Playwright) — navigate, extract text, click, type — until the task is done."
      />

      <div className="space-y-4">
        <Card title="Task">
          <TextInput value={task} onChange={setTask} />
          <div className="mt-2">
            <Button onClick={run} disabled={loading}>
              {loading ? "Running (this drives a real browser)..." : "Run agent"}
            </Button>
          </div>
          <div className="mt-2">
            <StatusLine text={error} error />
          </div>
        </Card>

        {result && (
          <Card title={`Result (${result.status})`}>
            <div className="rounded-lg bg-neutral-950 p-3 text-sm text-neutral-200">{result.answer}</div>
            <div className="mt-3 space-y-1.5">
              {result.actions.map((a, i) => (
                <div key={i} className="rounded-lg border border-neutral-800 p-2 text-xs">
                  <p className="text-neutral-300">
                    <span className="text-blue-400">{a.tool}</span>({JSON.stringify(a.input)})
                  </p>
                  <p className="mt-0.5 text-neutral-500">{a.result}</p>
                </div>
              ))}
            </div>
          </Card>
        )}
      </div>
    </div>
  );
}
