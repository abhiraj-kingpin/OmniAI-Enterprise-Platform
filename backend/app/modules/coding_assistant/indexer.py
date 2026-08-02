"""Repository Search / RAG-for-code: reuses the Enterprise RAG module's
chunking, hybrid search, and ONNX embedding store rather than standing up a
second search stack — a GitHub repo's source files are just documents with
a different chunking granularity."""

import uuid

from app.modules.coding_assistant.github_client import fetch_file_content, list_python_files
from app.modules.coding_assistant.schemas import CodeSearchResult
from app.modules.rag.chunking import chunk_text
from app.modules.rag.retrieval import hybrid_search
from app.modules.rag.store import get_collection


def collection_name_for(owner: str, repo: str) -> str:
    return f"code__{owner}__{repo}"


def index_github_repo(owner: str, repo: str, branch: str, max_files: int) -> tuple[int, int]:
    paths = list_python_files(owner, repo, branch, max_files=max_files)
    collection = get_collection(collection_name_for(owner, repo))

    total_chunks = 0
    files_indexed = 0
    for path in paths:
        try:
            content = fetch_file_content(owner, repo, branch, path)
        except Exception:
            continue
        chunks = chunk_text(content, chunk_chars=1500, overlap_chars=150)
        total_chunks += collection.add_document(str(uuid.uuid4()), path, chunks)
        files_indexed += 1

    return files_indexed, total_chunks


def search_code(collection_name: str, query: str, top_k: int = 5) -> list[CodeSearchResult]:
    collection = get_collection(collection_name)
    results = hybrid_search(collection, query, top_k=top_k, rerank=True)
    return [
        CodeSearchResult(
            source=r.chunk.source,
            text=r.chunk.text,
            score=r.rerank_score if r.rerank_score is not None else r.fused_score,
        )
        for r in results
    ]
