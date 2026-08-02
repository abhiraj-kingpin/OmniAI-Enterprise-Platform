"""Thin wrapper around the arXiv API (via the `arxiv` package)."""

import arxiv

from app.modules.research_assistant.schemas import Paper

_client = arxiv.Client()


def _to_paper(result: arxiv.Result) -> Paper:
    return Paper(
        arxiv_id=result.get_short_id(),
        title=result.title,
        authors=[a.name for a in result.authors],
        abstract=result.summary.replace("\n", " ").strip(),
        pdf_url=result.pdf_url,
        published=result.published.isoformat(),
    )


def search(query: str, max_results: int = 5) -> list[Paper]:
    search_obj = arxiv.Search(
        query=query, max_results=max_results, sort_by=arxiv.SortCriterion.Relevance
    )
    return [_to_paper(r) for r in _client.results(search_obj)]


def get_by_id(arxiv_id: str) -> Paper | None:
    search_obj = arxiv.Search(id_list=[arxiv_id])
    results = list(_client.results(search_obj))
    return _to_paper(results[0]) if results else None
