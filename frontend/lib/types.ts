/** Matches backend/app/core/availability.py's AvailabilityResponse — used
 * by any module gated behind a host-dependent capability check. */
export interface Availability {
  available: boolean;
  reason?: string | null;
}

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
