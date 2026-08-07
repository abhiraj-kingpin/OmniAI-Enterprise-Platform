from app.modules.research_assistant.schemas import Paper
from app.providers.factory import get_provider
from app.providers.types import AIMessage


async def summarize_paper(paper: Paper) -> str:
    response = await get_provider().complete(
        messages=[AIMessage(role="user", content=f"Title: {paper.title}\n\nAbstract: {paper.abstract}")],
        system=(
            "Summarize the research paper for a technically literate reader "
            "who hasn't read it: the problem, the approach, and the key "
            "result. 3-5 sentences, no headers."
        ),
        max_tokens=512,
    )
    return response.text


async def synthesize(question: str, papers: list[Paper]) -> str:
    """Knowledge Synthesis: compare/contrast multiple papers against a
    research question, rather than summarizing each in isolation."""
    sources = "\n\n".join(
        f"[{p.arxiv_id}] {p.title}\nAuthors: {', '.join(p.authors)}\nAbstract: {p.abstract}"
        for p in papers
    )
    response = await get_provider().complete(
        messages=[AIMessage(role="user", content=f"Question: {question}\n\nPapers:\n{sources}")],
        system=(
            "You are a research assistant. Given a question and a set of "
            "papers (with arXiv IDs), write a synthesis that directly "
            "answers the question, comparing/contrasting what the papers "
            "say and noting disagreement or gaps. Cite papers inline by "
            "arXiv ID in brackets, e.g. [2301.12345]."
        ),
        max_tokens=1500,
    )
    return response.text
