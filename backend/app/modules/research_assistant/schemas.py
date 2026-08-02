from pydantic import BaseModel


class Paper(BaseModel):
    arxiv_id: str
    title: str
    authors: list[str]
    abstract: str
    pdf_url: str
    published: str


class SearchRequest(BaseModel):
    query: str
    max_results: int = 5


class SearchResponse(BaseModel):
    query: str
    papers: list[Paper]


class SummarizeRequest(BaseModel):
    arxiv_id: str


class SummarizeResponse(BaseModel):
    paper: Paper
    summary: str


class SynthesizeRequest(BaseModel):
    question: str
    arxiv_ids: list[str]


class SynthesizeResponse(BaseModel):
    question: str
    papers: list[Paper]
    synthesis: str


class CitationsResponse(BaseModel):
    arxiv_id: str
    citations: list[str]


class AssistantRequest(BaseModel):
    question: str
    max_searches: int = 3


class AssistantResponse(BaseModel):
    question: str
    answer: str
    papers_consulted: list[Paper]
    search_queries_used: list[str]
