import anthropic

from app.modules.research_assistant.schemas import Paper


async def summarize_paper(paper: Paper) -> str:
    client = anthropic.AsyncAnthropic()
    response = await client.messages.create(
        model="claude-opus-5",
        max_tokens=512,
        system=(
            "Summarize the research paper for a technically literate reader "
            "who hasn't read it: the problem, the approach, and the key "
            "result. 3-5 sentences, no headers."
        ),
        messages=[
            {
                "role": "user",
                "content": f"Title: {paper.title}\n\nAbstract: {paper.abstract}",
            }
        ],
    )
    return next(b.text for b in response.content if b.type == "text")


async def synthesize(question: str, papers: list[Paper]) -> str:
    """Knowledge Synthesis: compare/contrast multiple papers against a
    research question, rather than summarizing each in isolation."""
    sources = "\n\n".join(
        f"[{p.arxiv_id}] {p.title}\nAuthors: {', '.join(p.authors)}\nAbstract: {p.abstract}"
        for p in papers
    )
    client = anthropic.AsyncAnthropic()
    response = await client.messages.create(
        model="claude-opus-5",
        max_tokens=1500,
        system=(
            "You are a research assistant. Given a question and a set of "
            "papers (with arXiv IDs), write a synthesis that directly "
            "answers the question, comparing/contrasting what the papers "
            "say and noting disagreement or gaps. Cite papers inline by "
            "arXiv ID in brackets, e.g. [2301.12345]."
        ),
        messages=[{"role": "user", "content": f"Question: {question}\n\nPapers:\n{sources}"}],
    )
    return next(b.text for b in response.content if b.type == "text")
