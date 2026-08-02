from pydantic import BaseModel


class GenerateRequest(BaseModel):
    prompt: str
    language: str = "python"


class GenerateResponse(BaseModel):
    code: str
    explanation: str


class ExplainRequest(BaseModel):
    code: str
    language: str = "python"


class ExplainResponse(BaseModel):
    explanation: str


class GenerateTestsRequest(BaseModel):
    code: str
    framework: str = "pytest"


class GenerateTestsResponse(BaseModel):
    tests: str


class FunctionInfo(BaseModel):
    name: str
    args: list[str]
    docstring: str | None
    lineno: int
    is_async: bool


class ClassInfo(BaseModel):
    name: str
    bases: list[str]
    methods: list[str]
    docstring: str | None
    lineno: int


class AstAnalysis(BaseModel):
    imports: list[str]
    functions: list[FunctionInfo]
    classes: list[ClassInfo]
    line_count: int
    approx_complexity: int


class AnalyzeRequest(BaseModel):
    code: str


class GithubRepoInfo(BaseModel):
    full_name: str
    description: str | None
    stars: int
    default_branch: str
    language: str | None


class IndexRepoRequest(BaseModel):
    owner: str
    repo: str
    max_files: int = 30


class IndexRepoResponse(BaseModel):
    collection: str
    files_indexed: int
    chunks_indexed: int


class SearchRepoRequest(BaseModel):
    collection: str
    query: str
    top_k: int = 5


class CodeSearchResult(BaseModel):
    source: str
    text: str
    score: float


class SearchRepoResponse(BaseModel):
    query: str
    results: list[CodeSearchResult]
