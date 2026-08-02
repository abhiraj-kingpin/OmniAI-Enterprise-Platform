"use client";

import type { Provider } from "@/lib/types";

const MODELS: Record<Provider, { id: string; label: string }[]> = {
  anthropic: [
    { id: "claude-opus-5", label: "Claude Opus 5" },
    { id: "claude-sonnet-5", label: "Claude Sonnet 5" },
    { id: "claude-haiku-4-5", label: "Claude Haiku 4.5" },
  ],
  openai: [
    { id: "gpt-4o", label: "GPT-4o" },
    { id: "gpt-4o-mini", label: "GPT-4o mini" },
  ],
};

interface Props {
  provider: Provider;
  model: string;
  onChange: (provider: Provider, model: string) => void;
}

export default function ModelSelector({ provider, model, onChange }: Props) {
  return (
    <div className="flex gap-2">
      <select
        value={provider}
        onChange={(e) => {
          const nextProvider = e.target.value as Provider;
          onChange(nextProvider, MODELS[nextProvider][0].id);
        }}
        className="rounded-md border border-neutral-700 bg-neutral-900 px-2 py-1 text-sm"
      >
        <option value="anthropic">Anthropic</option>
        <option value="openai">OpenAI</option>
      </select>
      <select
        value={model}
        onChange={(e) => onChange(provider, e.target.value)}
        className="rounded-md border border-neutral-700 bg-neutral-900 px-2 py-1 text-sm"
      >
        {MODELS[provider].map((m) => (
          <option key={m.id} value={m.id}>
            {m.label}
          </option>
        ))}
      </select>
    </div>
  );
}
