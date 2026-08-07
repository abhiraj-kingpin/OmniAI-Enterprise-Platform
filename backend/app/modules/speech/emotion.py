"""Emotion Detection — from the transcript's language, via an LLM, not from
acoustic prosody (pitch/energy/tempo). A real prosodic emotion classifier is
a trained model (again, PyTorch-based tooling); this is the honest
alternative available without one: what the words themselves convey.
"""

import json

from app.providers.factory import get_provider
from app.providers.types import AIMessage

_EMOTIONS = ["joy", "sadness", "anger", "fear", "surprise", "neutral"]

_SCHEMA = {
    "type": "object",
    "properties": {
        "primary_emotion": {"type": "string", "enum": _EMOTIONS},
        "scores": {
            "type": "object",
            "properties": {e: {"type": "number"} for e in _EMOTIONS},
            "required": _EMOTIONS,
            "additionalProperties": False,
        },
        "reasoning": {"type": "string"},
    },
    "required": ["primary_emotion", "scores", "reasoning"],
    "additionalProperties": False,
}


async def analyze_emotion(transcript: str) -> dict:
    response = await get_provider().complete(
        messages=[AIMessage(role="user", content=transcript)],
        system=(
            "Analyze the emotional tone of this speech transcript based on "
            "word choice, phrasing, and content. Score each emotion 0-1 "
            "(they don't need to sum to 1). Note in your reasoning that this "
            "is text-based, not acoustic (you can't hear tone of voice)."
        ),
        max_tokens=512,
        response_schema=_SCHEMA,
    )
    return json.loads(response.text)
