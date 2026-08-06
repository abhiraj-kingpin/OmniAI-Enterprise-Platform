const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export class ApiError extends Error {}

/** Matches the {"error": {"code", "message"}} envelope every backend error
 * response uses (see backend/app/core/exceptions.py). */
interface ApiErrorBody {
  error?: { code?: string; message?: string };
  detail?: string;
}

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body: ApiErrorBody = await res.json().catch(() => ({}));
    const message = body.error?.message ?? body.detail ?? res.statusText ?? `Request failed: ${res.status}`;
    throw new ApiError(message);
  }
  return res.json() as Promise<T>;
}

export async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  return handle<T>(res);
}

export async function apiPost<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: body !== undefined ? { "Content-Type": "application/json" } : undefined,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  return handle<T>(res);
}

export async function apiUpload<T>(path: string, form: FormData): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { method: "POST", body: form });
  return handle<T>(res);
}

export function apiFileUrl(path: string): string {
  return `${API_BASE}${path}`;
}

export { API_BASE };
