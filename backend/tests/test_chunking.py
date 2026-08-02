from app.modules.rag.chunking import chunk_text


def test_empty_text_returns_no_chunks():
    assert chunk_text("") == []
    assert chunk_text("   ") == []


def test_short_text_is_one_chunk():
    text = "This is a short sentence."
    chunks = chunk_text(text, chunk_chars=1200)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_long_text_splits_into_multiple_chunks():
    word = "banana "
    text = word * 500  # ~3500 chars
    chunks = chunk_text(text, chunk_chars=1000, overlap_chars=100)
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk) <= 1200  # allow slack for word-boundary rounding


def test_chunks_overlap():
    word_list = [f"word{i}" for i in range(400)]
    text = " ".join(word_list)
    chunks = chunk_text(text, chunk_chars=500, overlap_chars=100)
    assert len(chunks) > 1
    # the tail of chunk N should share some words with the head of chunk N+1
    tail_words = set(chunks[0].split()[-5:])
    head_words = set(chunks[1].split()[:20])
    assert tail_words & head_words
