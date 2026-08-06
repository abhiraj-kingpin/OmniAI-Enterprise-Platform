export interface ModuleInfo {
  href: string;
  name: string;
  description: string;
  skills: string[];
}

export const MODULES: ModuleInfo[] = [
  { href: "/chat", name: "Multi-LLM Chat", description: "Streaming chat across Anthropic and OpenAI, with function calling and memory.", skills: ["LLMs", "Function Calling", "Streaming"] },
  { href: "/rag", name: "Enterprise RAG", description: "Upload documents, hybrid BM25 + dense search, cross-encoder reranking, cited Q&A.", skills: ["Hybrid Search", "Embeddings", "Re-ranking"] },
  { href: "/vision", name: "Computer Vision", description: "Face/edge detection, OCR, CLIP-based product search, Claude vision captioning.", skills: ["OpenCV", "CLIP", "OCR"] },
  { href: "/speech", name: "Speech AI", description: "Whisper transcription, offline text-to-speech, speaker comparison, emotion analysis.", skills: ["Whisper", "TTS", "Speaker ID"] },
  { href: "/recommendations", name: "Recommendation System", description: "Matrix factorization collaborative filtering with candidate ranking.", skills: ["Collaborative Filtering", "Embeddings"] },
  { href: "/forecasting", name: "Forecasting", description: "Time series forecasting with ETS/ARIMA and engineered lag features.", skills: ["Time Series", "Feature Engineering"] },
  { href: "/coding", name: "AI Coding Assistant", description: "AST analysis, GitHub repo indexing and search, code generation and tests.", skills: ["AST Parsing", "GitHub API"] },
  { href: "/data-analyst", name: "AI Data Analyst", description: "Upload spreadsheets, run real SQL via DuckDB, auto-generate charts and insights.", skills: ["Pandas", "SQL", "Charts"] },
  { href: "/research", name: "AI Research Assistant", description: "arXiv search, a self-directed multi-search agent, citation extraction.", skills: ["Agents", "Citation Extraction"] },
  { href: "/image-gen", name: "AI Image Generator", description: "Real Stable Diffusion pipeline (text-to-image, LoRA, inpainting, ControlNet).", skills: ["Diffusion Models", "LoRA"] },
  { href: "/video-gen", name: "AI Video Generator", description: "Real optical-flow frame interpolation, plus a text-to-video diffusion pipeline.", skills: ["Frame Interpolation", "Diffusion"] },
  { href: "/browser-agent", name: "Autonomous Browser Agent", description: "Claude drives a real headless Chromium browser via Playwright to complete tasks.", skills: ["Playwright", "Planning"] },
  { href: "/finetune", name: "Fine-Tuning", description: "Real LoRA fine-tuning pipeline (PEFT + Transformers) with job tracking.", skills: ["LoRA", "PEFT"] },
  { href: "/mlops", name: "MLOps Dashboard", description: "Real MLflow experiment tracking, plus Docker/K8s/Airflow/DVC/CI artifacts.", skills: ["MLflow", "CI/CD"] },
  { href: "/distributed", name: "Distributed AI Infrastructure", description: "Live Ray cluster, Celery/Redis, Kafka, Spark — honest per-component status.", skills: ["Ray", "Kafka", "Celery"] },
];
