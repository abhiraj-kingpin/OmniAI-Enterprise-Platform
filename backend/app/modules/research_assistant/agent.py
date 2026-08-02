"""Multi-agent-style research loop: Claude drives its own literature search
via a search_arxiv tool, then writes a cited answer once it has enough.

Same tool-use-loop shape as the chat module's AnthropicProvider, scoped to
one domain-specific tool instead of a general toolbox.
"""

from typing import Any

import anthropic

from app.modules.research_assistant.arxiv_client import search as arxiv_search
from app.modules.research_assistant.schemas import AssistantResponse, Paper

_SEARCH_TOOL = {
    "name": "search_arxiv",
    "description": (
        "Search arXiv for papers relevant to a query. Returns up to 5 papers "
        "with title, authors, abstract, and arXiv ID. Call this whenever you "
        "need evidence for a claim rather than answering from memory."
    ),
    "input_schema": {
        "type": "object",
        "properties": {"query": {"type": "string", "description": "arXiv search query"}},
        "required": ["query"],
    },
}

SYSTEM_PROMPT = (
    "You are a research assistant. Use the search_arxiv tool to find real "
    "papers before answering — do not invent citations. Once you have "
    "enough evidence, answer the question directly and cite papers inline "
    "by arXiv ID in brackets, e.g. [2301.12345]."
)


async def run_research_assistant(question: str, max_searches: int = 3) -> AssistantResponse:
    client = anthropic.AsyncAnthropic()
    conversation: list[dict[str, Any]] = [{"role": "user", "content": question}]

    papers_by_id: dict[str, Paper] = {}
    queries_used: list[str] = []
    searches_done = 0

    while True:
        response = await client.messages.create(
            model="claude-opus-5",
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            tools=[_SEARCH_TOOL],
            messages=conversation,
        )
        conversation.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use" or searches_done >= max_searches:
            answer = next(
                (b.text for b in response.content if b.type == "text"),
                "I couldn't find enough information to answer confidently.",
            )
            return AssistantResponse(
                question=question,
                answer=answer,
                papers_consulted=list(papers_by_id.values()),
                search_queries_used=queries_used,
            )

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            query = block.input.get("query", question)
            queries_used.append(query)
            searches_done += 1

            results = arxiv_search(query, max_results=5)
            for p in results:
                papers_by_id[p.arxiv_id] = p

            summary = "\n".join(f"[{p.arxiv_id}] {p.title} — {p.abstract[:200]}..." for p in results)
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": summary or "No results found.",
                }
            )
        conversation.append({"role": "user", "content": tool_results})
