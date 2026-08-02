export type Role = "user" | "assistant";

export interface ChatMessage {
  role: Role;
  content: string;
}

export type Provider = "anthropic" | "openai";

export interface StreamChunk {
  type: "text" | "tool_use" | "tool_result" | "usage" | "done" | "error";
  content?: string;
  name?: string;
  input?: Record<string, unknown>;
  usage?: { input_tokens: number; output_tokens: number };
  message?: string;
}
