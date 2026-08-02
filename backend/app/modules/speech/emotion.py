"""Emotion Detection — from the transcript's language, via Claude, not from
acoustic prosody (pitch/energy/tempo). A real prosodic emotion classifier is
a trained model (again, PyTorch-based tooling); this is the honest
alternative available without one: what the words themselves convey.
"""

import json

import anthropic

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
    client = anthropic.AsyncAnthropic()
    response = await client.messages.create(
        model="claude-opus-5",
        max_tokens=512,
        system=(
            "Analyze the emotional tone of this speech transcript based on "
            "word choice, phrasing, and content. Score each emotion 0-1 "
            "(they don't need to sum to 1). Note in your reasoning that this "
            "is text-based, not acoustic (you can't hear tone of voice)."
        ),
        messages=[{"role": "user", "content": transcript}],
        output_config={"format": {"type": "json_schema", "schema": _SCHEMA}},
    )
    text_block = next(b.text for b in response.content if b.type == "text")
    return json.loads(text_block)
