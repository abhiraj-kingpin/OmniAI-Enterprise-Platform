"""Text-to-Speech via pyttsx3, which drives Windows SAPI5 directly — no
model download, no torch, genuinely offline."""

import tempfile
from pathlib import Path

from app.modules.speech.schemas import VoiceInfo


def list_voices() -> list[VoiceInfo]:
    import pyttsx3

    engine = pyttsx3.init()
    try:
        voices = engine.getProperty("voices")
        return [
            VoiceInfo(index=i, name=v.name, languages=[str(lang) for lang in (v.languages or [])])
            for i, v in enumerate(voices)
        ]
    finally:
        engine.stop()


def synthesize(text: str, rate: int, voice_index: int) -> bytes:
    import pyttsx3

    engine = pyttsx3.init()
    try:
        engine.setProperty("rate", rate)
        voices = engine.getProperty("voices")
        if voices and 0 <= voice_index < len(voices):
            engine.setProperty("voice", voices[voice_index].id)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name

        engine.save_to_file(text, tmp_path)
        engine.runAndWait()

        audio_bytes = Path(tmp_path).read_bytes()
        Path(tmp_path).unlink(missing_ok=True)
        return audio_bytes
    finally:
        engine.stop()
