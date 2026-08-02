"""Fixed-size, word-boundary-aware chunking with overlap.

A production system would chunk semantically (by heading, by paragraph
boundary, token-aware) — this is the simple, robust default that works
uniformly across every source type ingest.py produces.
"""

DEFAULT_CHUNK_CHARS = 1200
DEFAULT_OVERLAP_CHARS = 200


def chunk_text(
    text: str,
    chunk_chars: int = DEFAULT_CHUNK_CHARS,
    overlap_chars: int = DEFAULT_OVERLAP_CHARS,
) -> list[str]:
    text = text.strip()
    if not text:
        return []

    words = text.split()
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for word in words:
        current.append(word)
        current_len += len(word) + 1
        if current_len >= chunk_chars:
            chunks.append(" ".join(current))
            # Keep the tail of this chunk as the start of the next one,
            # measured in characters, so context isn't lost at the boundary.
            tail: list[str] = []
            tail_len = 0
            for w in reversed(current):
                tail_len += len(w) + 1
                tail.insert(0, w)
                if tail_len >= overlap_chars:
                    break
            current = tail
            current_len = tail_len

    if current:
        chunks.append(" ".join(current))

    return chunks
