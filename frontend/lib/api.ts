import type { Provider, StreamChunk } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export interface SendMessageArgs {
  sessionId: string;
  provider: Provider;
  model: string;
  message: string;
  onChunk: (chunk: StreamChunk) => void;
  signal?: AbortSignal;
}

/**
 * POSTs a user message and streams the assistant's reply back as
 * newline-delimited SSE ("data: {...}\n\n" frames). EventSource can't be
 * used here since it only supports GET — this reads the fetch response body
 * as a stream instead and parses SSE frames by hand.
 */
export async function sendMessage({
  sessionId,
  provider,
  model,
  message,
  onChunk,
  signal,
}: SendMessageArgs): Promise<void> {
  const res = await fetch(`${API_BASE}/api/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: sessionId,
      provider,
      model,
      message,
    }),
    signal,
  });

  if (!res.ok || !res.body) {
    throw new Error(`Chat request failed: ${res.status}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const frames = buffer.split("\n\n");
    buffer = frames.pop() ?? "";

    for (const frame of frames) {
      const line = frame.trim();
      if (!line.startsWith("data:")) continue;
      const json = line.slice("data:".length).trim();
      if (!json) continue;
      onChunk(JSON.parse(json) as StreamChunk);
    }
  }
}
