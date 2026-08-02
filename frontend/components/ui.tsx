"use client";

import type { ReactNode } from "react";

export function Card({ title, children }: { title?: string; children: ReactNode }) {
  return (
    <div className="rounded-xl border border-neutral-800 bg-neutral-900/50 p-4">
      {title && <h2 className="mb-3 text-sm font-semibold text-neutral-200">{title}</h2>}
      {children}
    </div>
  );
}

export function Button({
  children,
  onClick,
  disabled,
  variant = "primary",
  type = "button",
}: {
  children: ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  variant?: "primary" | "secondary";
  type?: "button" | "submit";
}) {
  const base = "rounded-lg px-4 py-2 text-sm font-medium disabled:opacity-50 transition-colors";
  const styles =
    variant === "primary"
      ? "bg-blue-600 hover:bg-blue-500 text-white"
      : "bg-neutral-800 hover:bg-neutral-700 text-neutral-100 border border-neutral-700";
  return (
    <button type={type} onClick={onClick} disabled={disabled} className={`${base} ${styles}`}>
      {children}
    </button>
  );
}

export function TextInput({
  value,
  onChange,
  placeholder,
  className = "",
}: {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  className?: string;
}) {
  return (
    <input
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      className={`w-full rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm outline-none focus:border-blue-500 ${className}`}
    />
  );
}

export function TextArea({
  value,
  onChange,
  placeholder,
  rows = 4,
}: {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  rows?: number;
}) {
  return (
    <textarea
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      rows={rows}
      className="w-full rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm outline-none focus:border-blue-500"
    />
  );
}

export function FileInput({
  onSelect,
  accept,
  label = "Choose file",
}: {
  onSelect: (file: File) => void;
  accept?: string;
  label?: string;
}) {
  return (
    <label className="flex cursor-pointer items-center justify-center rounded-lg border border-dashed border-neutral-700 px-3 py-4 text-sm text-neutral-400 hover:border-blue-500 hover:text-neutral-200">
      {label}
      <input
        type="file"
        accept={accept}
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) onSelect(file);
        }}
      />
    </label>
  );
}

export function StatusLine({ text, error }: { text: string | null; error?: boolean }) {
  if (!text) return null;
  return <p className={`text-xs ${error ? "text-red-400" : "text-neutral-500"}`}>{text}</p>;
}

export function JsonView({ data }: { data: unknown }) {
  return (
    <pre className="max-h-96 overflow-auto rounded-lg bg-neutral-950 p-3 text-xs text-neutral-300">
      {JSON.stringify(data, null, 2)}
    </pre>
  );
}

export function PageHeader({ title, description }: { title: string; description: string }) {
  return (
    <header className="mb-6">
      <h1 className="text-xl font-semibold text-neutral-100">{title}</h1>
      <p className="mt-1 text-sm text-neutral-500">{description}</p>
    </header>
  );
}
