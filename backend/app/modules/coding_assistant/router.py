from fastapi import APIRouter, HTTPException

from app.modules.coding_assistant.ast_analysis import analyze
from app.modules.coding_assistant.generation import explain_code, generate_code, generate_tests
from app.modules.coding_assistant.github_client import get_repo_info
from app.modules.coding_assistant.indexer import collection_name_for, index_github_repo, search_code
from app.modules.coding_assistant.schemas import (
    AnalyzeRequest,
    AstAnalysis,
    ExplainRequest,
    ExplainResponse,
    GenerateRequest,
    GenerateResponse,
    GenerateTestsRequest,
    GenerateTestsResponse,
    GithubRepoInfo,
    IndexRepoRequest,
    IndexRepoResponse,
    SearchRepoRequest,
    SearchRepoResponse,
)

router = APIRouter()


@router.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest) -> GenerateResponse:
    code, explanation = await generate_code(req.prompt, req.language)
    return GenerateResponse(code=code, explanation=explanation)


@router.post("/explain", response_model=ExplainResponse)
async def explain(req: ExplainRequest) -> ExplainResponse:
    return ExplainResponse(explanation=await explain_code(req.code, req.language))


@router.post("/generate-tests", response_model=GenerateTestsResponse)
async def tests(req: GenerateTestsRequest) -> GenerateTestsResponse:
    return GenerateTestsResponse(tests=await generate_tests(req.code, req.framework))


@router.post("/analyze", response_model=AstAnalysis)
async def analyze_code(req: AnalyzeRequest) -> AstAnalysis:
    try:
        return analyze(req.code)
    except SyntaxError as exc:
        raise HTTPException(400, f"Not valid Python: {exc}") from exc


@router.get("/github/{owner}/{repo}", response_model=GithubRepoInfo)
async def github_repo_info(owner: str, repo: str) -> GithubRepoInfo:
    try:
        return get_repo_info(owner, repo)
    except Exception as exc:
        raise HTTPException(404, f"Couldn't fetch {owner}/{repo}: {exc}") from exc


@router.post("/github/index", response_model=IndexRepoResponse)
async def github_index(req: IndexRepoRequest) -> IndexRepoResponse:
    try:
        info = get_repo_info(req.owner, req.repo)
    except Exception as exc:
        raise HTTPException(404, f"Couldn't fetch {req.owner}/{req.repo}: {exc}") from exc

    files_indexed, chunks_indexed = index_github_repo(
        req.owner, req.repo, info.default_branch, req.max_files
    )
    return IndexRepoResponse(
        collection=collection_name_for(req.owner, req.repo),
        files_indexed=files_indexed,
        chunks_indexed=chunks_indexed,
    )


@router.post("/search", response_model=SearchRepoResponse)
async def search(req: SearchRepoRequest) -> SearchRepoResponse:
    results = search_code(req.collection, req.query, top_k=req.top_k)
    return SearchRepoResponse(query=req.query, results=results)
