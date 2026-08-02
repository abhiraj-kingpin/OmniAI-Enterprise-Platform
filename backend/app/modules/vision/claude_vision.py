"""Claude's multimodal vision for the tasks that genuinely need semantic
understanding rather than pixel-level processing: captioning, open-set
classification, and object description. Real object *detection* (YOLO) and
segmentation (SAM) are PyTorch-only with no practical ONNX path we could
stand up here — blocked by this host's Smart App Control policy, same as
Fine-Tuning and Image Generation. This is the honest substitute: Claude can
describe and enumerate what it sees, just not emit pixel-accurate boxes/masks.
"""

import base64
import json

import anthropic

_JSON_ARRAY_SCHEMA = {
    "type": "object",
    "properties": {"objects": {"type": "array", "items": {"type": "string"}}},
    "required": ["objects"],
    "additionalProperties": False,
}


def _image_block(image_bytes: bytes, media_type: str) -> dict:
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": media_type,
            "data": base64.standard_b64encode(image_bytes).decode("ascii"),
        },
    }


async def caption(image_bytes: bytes, media_type: str) -> str:
    client = anthropic.AsyncAnthropic()
    response = await client.messages.create(
        model="claude-opus-5",
        max_tokens=256,
        messages=[
            {
                "role": "user",
                "content": [
                    _image_block(image_bytes, media_type),
                    {"type": "text", "text": "Caption this image in one concise sentence."},
                ],
            }
        ],
    )
    return next(b.text for b in response.content if b.type == "text").strip()


async def classify(image_bytes: bytes, media_type: str, categories: list[str]) -> str:
    client = anthropic.AsyncAnthropic()
    response = await client.messages.create(
        model="claude-opus-5",
        max_tokens=50,
        system=(
            f"Classify the image into exactly one of these categories: "
            f"{', '.join(categories)}. Respond with only the category name."
        ),
        messages=[{"role": "user", "content": [_image_block(image_bytes, media_type)]}],
    )
    return next(b.text for b in response.content if b.type == "text").strip()


async def detect_objects(image_bytes: bytes, media_type: str) -> tuple[list[str], str]:
    client = anthropic.AsyncAnthropic()
    response = await client.messages.create(
        model="claude-opus-5",
        max_tokens=512,
        system=(
            "Describe the spatial arrangement of objects in the image in one "
            "paragraph: roughly where each one is (left/right/center, "
            "foreground/background) relative to the others."
        ),
        messages=[{"role": "user", "content": [_image_block(image_bytes, media_type)]}],
    )
    detail = next(b.text for b in response.content if b.type == "text").strip()

    # Second, cheap call for a clean structured object list (keeps the
    # detail paragraph free-form while the list stays machine-readable).
    structured = await client.messages.create(
        model="claude-opus-5",
        max_tokens=256,
        messages=[
            {
                "role": "user",
                "content": [
                    _image_block(image_bytes, media_type),
                    {"type": "text", "text": "List distinct objects visible, as short noun phrases."},
                ],
            }
        ],
        output_config={"format": {"type": "json_schema", "schema": _JSON_ARRAY_SCHEMA}},
    )
    structured_text = next(b.text for b in structured.content if b.type == "text")
    objects = json.loads(structured_text)["objects"]

    return objects, detail
