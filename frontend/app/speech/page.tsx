"use client";

import { useState } from "react";

import { API_BASE, apiUpload } from "@/lib/backend";
import { Button, Card, FileInput, PageHeader, StatusLine, TextArea } from "@/components/ui";

interface TranscribeResponse {
  text: string;
  language: string;
}

export default function SpeechPage() {
  const [text, setText] = useState("The quick brown fox jumps over the lazy dog.");
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [ttsStatus, setTtsStatus] = useState<string | null>(null);

  const [transcript, setTranscript] = useState<TranscribeResponse | null>(null);
  const [sttStatus, setSttStatus] = useState<string | null>(null);

  async function synthesize() {
    setTtsStatus("Synthesizing...");
    try {
      const res = await fetch(`${API_BASE}/api/speech/synthesize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, rate: 175, voice_index: 0 }),
      });
      if (!res.ok) throw new Error(await res.text());
      const blob = await res.blob();
      setAudioUrl(URL.createObjectURL(blob));
      setTtsStatus(null);
    } catch (err) {
      setTtsStatus(err instanceof Error ? err.message : "Failed");
    }
  }

  async function transcribeFile(file: File) {
    setSttStatus(`Transcribing ${file.name}...`);
    const form = new FormData();
    form.append("file", file);
    try {
      const res = await apiUpload<TranscribeResponse>("/api/speech/transcribe", form);
      setTranscript(res);
      setSttStatus(null);
    } catch (err) {
      setSttStatus(err instanceof Error ? err.message : "Failed");
    }
  }

  return (
    <div className="mx-auto max-w-3xl p-8">
      <PageHeader
        title="Speech AI"
        description="Offline text-to-speech (Windows SAPI) and real Whisper transcription (faster-whisper) — try the round trip: synthesize, download, re-upload to transcribe."
      />

      <div className="space-y-4">
        <Card title="Text-to-Speech">
          <TextArea value={text} onChange={setText} rows={2} />
          <div className="mt-2">
            <Button onClick={synthesize}>Synthesize</Button>
          </div>
          <div className="mt-2">
            <StatusLine text={ttsStatus} error />
          </div>
          {audioUrl && (
            <audio controls src={audioUrl} className="mt-3 w-full">
              <track kind="captions" />
            </audio>
          )}
        </Card>

        <Card title="Speech-to-Text">
          <FileInput label="Upload a WAV/MP3 file" accept="audio/*" onSelect={transcribeFile} />
          <div className="mt-2">
            <StatusLine text={sttStatus} error />
          </div>
          {transcript && (
            <div className="mt-3 rounded-lg bg-neutral-950 p-3 text-sm text-neutral-200">
              <p className="mb-1 text-xs text-neutral-500">Detected language: {transcript.language}</p>
              {transcript.text}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
