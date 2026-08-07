"""Multi-agent-style research loop: the model drives its own literature
search via a search_arxiv tool, then writes a cited answer once it has
enough. Same tool-use-loop shape as the Chat module's providers, scoped to
one domain-specific tool instead of a general toolbox — and, like Chat,
provider-agnostic via app/providers/factory.py.
"""

from app.modules.research_assistant.arxiv_client import search as arxiv_search
from app.modules.research_assistant.schemas import AssistantResponse, Paper
from app.providers.factory import get_provider
from app.providers.types import AIMessage, ToolDefinition, ToolResult

_SEARCH_TOOL = ToolDefinition(
    name="search_arxiv",
    description=(
        "Search arXiv for papers relevant to a query. Returns up to 5 papers "
        "with title, authors, abstract, and arXiv ID. Call this whenever you "
        "need evidence for a claim rather than answering from memory."
    ),
    input_schema={
        "type": "object",
        "properties": {"query": {"type": "string", "description": "arXiv search query"}},
        "required": ["query"],
    },
)

SYSTEM_PROMPT = (
    "You are a research assistant. Use the search_arxiv tool to find real "
    "papers before answering — do not invent citations. Once you have "
    "enough evidence, answer the question directly and cite papers inline "
    "by arXiv ID in brackets, e.g. [2301.12345]."
)


async def run_research_assistant(question: str, max_searches: int = 3) -> AssistantResponse:
    provider = get_provider()
    conversation: list[AIMessage] = [AIMessage(role="user", content=question)]

    papers_by_id: dict[str, Paper] = {}
    queries_used: list[str] = []
    searches_done = 0

    while True:
        response = await provider.complete(
            messages=conversation, system=SYSTEM_PROMPT, max_tokens=2048, tools=[_SEARCH_TOOL]
        )
        conversation.append(AIMessage(role="assistant", content=response.text, tool_calls=response.tool_calls))

        if response.stop_reason != "tool_use" or searches_done >= max_searches:
            answer = response.text or "I couldn't find enough information to answer confidently."
            return AssistantResponse(
                question=question,
                answer=answer,
                papers_consulted=list(papers_by_id.values()),
                search_queries_used=queries_used,
            )

        tool_results: list[ToolResult] = []
        for call in response.tool_calls:
            query = call.input.get("query", question)
            queries_used.append(query)
            searches_done += 1

            results = arxiv_search(query, max_results=5)
            for p in results:
                papers_by_id[p.arxiv_id] = p

            summary = "\n".join(f"[{p.arxiv_id}] {p.title} — {p.abstract[:200]}..." for p in results)
            tool_results.append(ToolResult(tool_call_id=call.id, content=summary or "No results found."))
        conversation.append(AIMessage(role="user", content="", tool_results=tool_results))
