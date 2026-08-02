"""Citation extraction: download the paper PDF, pull text from the
references section, ask Claude to pull out a clean citation list."""

import io
import json

import anthropic
import pypdf
import requests

from app.modules.research_assistant.schemas import Paper

_CITATIONS_SCHEMA = {
    "type": "object",
    "properties": {
        "citations": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["citations"],
    "additionalProperties": False,
}


def _fetch_pdf_text(pdf_url: str) -> str:
    resp = requests.get(pdf_url, timeout=30, headers={"User-Agent": "OmniAI-Research/0.1"})
    resp.raise_for_status()
    reader = pypdf.PdfReader(io.BytesIO(resp.content))
    # References are almost always on the last few pages — reading the
    # whole PDF just to find them wastes tokens on a long paper.
    tail_pages = reader.pages[-4:] if len(reader.pages) > 4 else reader.pages
    return "\n".join(page.extract_text() or "" for page in tail_pages)


async def extract_citations(paper: Paper) -> list[str]:
    tail_text = _fetch_pdf_text(paper.pdf_url)

    client = anthropic.AsyncAnthropic()
    response = await client.messages.create(
        model="claude-opus-5",
        max_tokens=2048,
        system=(
            "This is the tail of an academic paper's PDF text, which should "
            "include its reference list. Extract each individual citation as "
            "a clean, single-line string (author, year, title — whatever the "
            "source format gives you). Ignore page headers/footers and body "
            "text that isn't a reference entry."
        ),
        messages=[{"role": "user", "content": tail_text[:15000]}],
        output_config={"format": {"type": "json_schema", "schema": _CITATIONS_SCHEMA}},
    )
    text_block = next(b for b in response.content if b.type == "text")
    return json.loads(text_block.text)["citations"]
