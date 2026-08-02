"use client";

import { useRef, useState } from "react";

import { sendMessage } from "@/lib/api";
import type { ChatMessage, Provider, StreamChunk } from "@/lib/types";

import MessageBubble from "./MessageBubble";
import ModelSelector from "./ModelSelector";

function newSessionId(): string {
  return crypto.randomUUID();
}

export default function Chat() {
  const [sessionId] = useState(newSessionId);
  const [provider, setProvider] = useState<Provider>("anthropic");
  const [model, setModel] = useState("claude-opus-5");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  function appendToLastAssistantMessage(text: string) {
    setMessages((prev) => {
      const next = [...prev];
      const last = next[next.length - 1];
      next[next.length - 1] = { ...last, content: last.content + text };
      return next;
    });
  }

  async function handleSend() {
    const text = input.trim();
    if (!text || isStreaming) return;

    setMessages((prev) => [
      ...prev,
      { role: "user", content: text },
      { role: "assistant", content: "" },
    ]);
    setInput("");
    setIsStreaming(true);
    setStatus(null);

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      await sendMessage({
        sessionId,
        provider,
        model,
        message: text,
        signal: controller.signal,
        onChunk: (chunk: StreamChunk) => {
          switch (chunk.type) {
            case "text":
              appendToLastAssistantMessage(chunk.content ?? "");
              break;
            case "tool_use":
              setStatus(`Using tool: ${chunk.name}…`);
              break;
            case "tool_result":
              setStatus(null);
              break;
            case "error":
              setStatus(`Error: ${chunk.message}`);
              break;
            case "usage":
            case "done":
              break;
          }
        },
      });
    } catch (err) {
      setStatus(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setIsStreaming(false);
    }
  }

  return (
    <div className="flex h-full flex-col gap-4 p-4">
      <header className="flex items-center justify-between border-b border-neutral-800 pb-3">
        <h1 className="text-lg font-semibold">OmniAI · Multi-LLM Chat</h1>
        <ModelSelector
          provider={provider}
          model={model}
          onChange={(p, m) => {
            setProvider(p);
            setModel(m);
          }}
        />
      </header>

      <div className="flex-1 space-y-3 overflow-y-auto">
        {messages.length === 0 && (
          <p className="mt-8 text-center text-sm text-neutral-500">
            Start a conversation — switch providers any time with the
            selector above.
          </p>
        )}
        {messages.map((m, i) => (
          <MessageBubble key={i} message={m} />
        ))}
        {status && <p className="text-xs text-neutral-500">{status}</p>}
      </div>

      <div className="flex gap-2 border-t border-neutral-800 pt-3">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
          placeholder="Ask anything…"
          className="flex-1 rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm outline-none focus:border-blue-500"
        />
        <button
          onClick={handleSend}
          disabled={isStreaming}
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium disabled:opacity-50"
        >
          Send
        </button>
      </div>
    </div>
  );
}
