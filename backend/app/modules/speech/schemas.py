from pydantic import BaseModel


class TranscriptSegment(BaseModel):
    start: float
    end: float
    text: str


class TranscribeResponse(BaseModel):
    language: str
    language_probability: float
    text: str
    segments: list[TranscriptSegment]


class SynthesizeRequest(BaseModel):
    text: str
    rate: int = 175
    voice_index: int = 0


class VoiceInfo(BaseModel):
    index: int
    name: str
    languages: list[str]


class SpeakerCompareResponse(BaseModel):
    similarity: float
    likely_same_speaker: bool


class EmotionResponse(BaseModel):
    transcript: str
    primary_emotion: str
    emotions: dict[str, float]
    reasoning: str
