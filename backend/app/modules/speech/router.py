from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile

from app.modules.speech.emotion import analyze_emotion
from app.modules.speech.schemas import (
    EmotionResponse,
    SpeakerCompareResponse,
    SynthesizeRequest,
    TranscribeResponse,
    VoiceInfo,
)
from app.modules.speech.speaker import compare
from app.modules.speech.stt import transcribe
from app.modules.speech.tts import list_voices, synthesize

router = APIRouter()


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(file: UploadFile = File(...)) -> TranscribeResponse:
    content = await file.read()
    suffix = Path(file.filename or "audio.wav").suffix or ".wav"
    try:
        return transcribe(content, suffix=suffix)
    except Exception as exc:
        raise HTTPException(400, f"Couldn't transcribe audio: {exc}") from exc


@router.get("/voices", response_model=list[VoiceInfo])
async def voices() -> list[VoiceInfo]:
    return list_voices()


@router.post("/synthesize")
async def synthesize_speech(req: SynthesizeRequest) -> Response:
    audio = synthesize(req.text, rate=req.rate, voice_index=req.voice_index)
    return Response(content=audio, media_type="audio/wav")


@router.post("/speaker/compare", response_model=SpeakerCompareResponse)
async def speaker_compare(
    file_a: UploadFile = File(...), file_b: UploadFile = File(...)
) -> SpeakerCompareResponse:
    audio_a, audio_b = await file_a.read(), await file_b.read()
    similarity = compare(audio_a, audio_b)
    return SpeakerCompareResponse(similarity=similarity, likely_same_speaker=similarity > 0.85)


@router.post("/emotion", response_model=EmotionResponse)
async def emotion(transcript: str = Form(...)) -> EmotionResponse:
    result = await analyze_emotion(transcript)
    return EmotionResponse(
        transcript=transcript,
        primary_emotion=result["primary_emotion"],
        emotions=result["scores"],
        reasoning=result["reasoning"],
    )
