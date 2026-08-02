from fastapi import APIRouter, HTTPException

from app.modules.research_assistant.agent import run_research_assistant
from app.modules.research_assistant.arxiv_client import get_by_id, search
from app.modules.research_assistant.citations import extract_citations
from app.modules.research_assistant.schemas import (
    AssistantRequest,
    AssistantResponse,
    CitationsResponse,
    SearchRequest,
    SearchResponse,
    SummarizeRequest,
    SummarizeResponse,
    SynthesizeRequest,
    SynthesizeResponse,
)
from app.modules.research_assistant.summarize import summarize_paper, synthesize

router = APIRouter()


@router.post("/search", response_model=SearchResponse)
async def search_papers(req: SearchRequest) -> SearchResponse:
    papers = search(req.query, max_results=req.max_results)
    return SearchResponse(query=req.query, papers=papers)


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize(req: SummarizeRequest) -> SummarizeResponse:
    paper = get_by_id(req.arxiv_id)
    if paper is None:
        raise HTTPException(404, f"arXiv paper '{req.arxiv_id}' not found")
    return SummarizeResponse(paper=paper, summary=await summarize_paper(paper))


@router.post("/synthesize", response_model=SynthesizeResponse)
async def synthesize_papers(req: SynthesizeRequest) -> SynthesizeResponse:
    papers = [p for p in (get_by_id(aid) for aid in req.arxiv_ids) if p is not None]
    if not papers:
        raise HTTPException(404, "None of the given arXiv IDs were found")
    return SynthesizeResponse(
        question=req.question, papers=papers, synthesis=await synthesize(req.question, papers)
    )


@router.get("/citations/{arxiv_id}", response_model=CitationsResponse)
async def citations(arxiv_id: str) -> CitationsResponse:
    paper = get_by_id(arxiv_id)
    if paper is None:
        raise HTTPException(404, f"arXiv paper '{arxiv_id}' not found")
    return CitationsResponse(arxiv_id=arxiv_id, citations=await extract_citations(paper))


@router.post("/assistant", response_model=AssistantResponse)
async def assistant(req: AssistantRequest) -> AssistantResponse:
    return await run_research_assistant(req.question, max_searches=req.max_searches)
