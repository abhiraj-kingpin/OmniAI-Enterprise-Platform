"""Multimodal LLM vision for the tasks that genuinely need semantic
understanding rather than pixel-level processing: captioning, open-set
classification, and object description. Real object *detection* (YOLO) and
segmentation (SAM) are PyTorch-only with no practical ONNX path we could
stand up here — blocked by this host's Smart App Control policy, same as
Fine-Tuning and Image Generation. This is the honest substitute: a
vision-capable LLM can describe and enumerate what it sees, just not emit
pixel-accurate boxes/masks. Works with whichever provider AI_PROVIDER
selects, provided that provider's model supports image input — see each
provider's docs in app/providers/ for which of its models do.
"""

import json

from app.providers.factory import get_provider
from app.providers.types import AIMessage, ImagePart, TextPart

_JSON_ARRAY_SCHEMA = {
    "type": "object",
    "properties": {"objects": {"type": "array", "items": {"type": "string"}}},
    "required": ["objects"],
    "additionalProperties": False,
}


async def caption(image_bytes: bytes, media_type: str) -> str:
    response = await get_provider().complete(
        messages=[
            AIMessage(
                role="user",
                content=[
                    ImagePart(data=image_bytes, media_type=media_type),
                    TextPart(text="Caption this image in one concise sentence."),
                ],
            )
        ],
        max_tokens=256,
    )
    return response.text.strip()


async def classify(image_bytes: bytes, media_type: str, categories: list[str]) -> str:
    response = await get_provider().complete(
        messages=[AIMessage(role="user", content=[ImagePart(data=image_bytes, media_type=media_type)])],
        system=(
            f"Classify the image into exactly one of these categories: "
            f"{', '.join(categories)}. Respond with only the category name."
        ),
        max_tokens=50,
    )
    return response.text.strip()


async def detect_objects(image_bytes: bytes, media_type: str) -> tuple[list[str], str]:
    provider = get_provider()
    image = ImagePart(data=image_bytes, media_type=media_type)

    detail_response = await provider.complete(
        messages=[AIMessage(role="user", content=[image])],
        system=(
            "Describe the spatial arrangement of objects in the image in one "
            "paragraph: roughly where each one is (left/right/center, "
            "foreground/background) relative to the others."
        ),
        max_tokens=512,
    )

    # Second, cheap call for a clean structured object list (keeps the
    # detail paragraph free-form while the list stays machine-readable).
    list_response = await provider.complete(
        messages=[
            AIMessage(
                role="user",
                content=[image, TextPart(text="List distinct objects visible, as short noun phrases.")],
            )
        ],
        max_tokens=256,
        response_schema=_JSON_ARRAY_SCHEMA,
    )
    objects = json.loads(list_response.text)["objects"]

    return objects, detail_response.text.strip()
