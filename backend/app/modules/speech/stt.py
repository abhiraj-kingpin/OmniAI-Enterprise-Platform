"""Speech-to-Text via faster-whisper — CTranslate2-based, not PyTorch, so it
passes this host's Smart App Control policy where openai-whisper (torch)
would not. Same real Whisper model weights, just a different runtime."""

import tempfile
from functools import lru_cache
from pathlib import Path

from app.modules.speech.schemas import TranscribeResponse, TranscriptSegment


@lru_cache(maxsize=1)
def _model():
    from faster_whisper import WhisperModel

    # "small" balances accuracy and speed well on CPU; drop to "tiny" or
    # "base" if transcription needs to be faster than realtime.
    return WhisperModel("small", device="cpu", compute_type="int8")


def transcribe(audio_bytes: bytes, suffix: str = ".wav") -> TranscribeResponse:
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        segments_iter, info = _model().transcribe(tmp_path, beam_size=5)
        segments = [
            TranscriptSegment(start=s.start, end=s.end, text=s.text.strip())
            for s in segments_iter
        ]
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    return TranscribeResponse(
        language=info.language,
        language_probability=info.language_probability,
        text=" ".join(s.text for s in segments),
        segments=segments,
    )
