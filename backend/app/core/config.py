import os
from pathlib import Path
from typing import Optional
from app.core.compat import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
STORAGE_DIR = DATA_DIR / "storage"
UPLOAD_DIR = DATA_DIR / "uploads"

# Ensure runtime directories exist
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def load_env_file():
    """Reads .env from backend directory or project root."""
    for env_path in [BASE_DIR / ".env", BASE_DIR.parent / ".env"]:
        if env_path.exists():
            try:
                for line in env_path.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip("'\"")
                        if k and k not in os.environ:
                            os.environ[k] = v
            except Exception:
                pass


load_env_file()


class Settings(BaseModel):
    PROJECT_NAME: str = "Advanced RAG Agent with Context Compression & Semantic Memory"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api"

    @property
    def GEMINI_API_KEY(self) -> str:
        return os.getenv("GEMINI_API_KEY", "")

    @property
    def COHERE_API_KEY(self) -> str:
        return os.getenv("COHERE_API_KEY", "")

    @property
    def MEM0_API_KEY(self) -> str:
        return os.getenv("MEM0_API_KEY", "")

    @property
    def QDRANT_URL(self) -> str:
        return os.getenv("QDRANT_URL", "")

    @property
    def QDRANT_API_KEY(self) -> str:
        return os.getenv("QDRANT_API_KEY", "")

    # RAG Settings
    PARENT_CHUNK_SIZE: int = 1000
    PARENT_CHUNK_OVERLAP: int = 100
    CHILD_CHUNK_SIZE: int = 200
    CHILD_CHUNK_OVERLAP: int = 30
    RRF_K: int = 60
    TOP_K_CANDIDATES: int = 20
    TOP_N_RERANK: int = 5
    RELEVANCE_SCORE_THRESHOLD: float = 0.01
    COHERE_RERANK_MODEL: str = "rerank-english-v3.0"

    @property
    def GEMINI_MODEL(self) -> str:
        return os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

    # Paths
    BASE_DIR: Path = BASE_DIR
    DATA_DIR: Path = DATA_DIR
    STORAGE_DIR: Path = STORAGE_DIR
    UPLOAD_DIR: Path = UPLOAD_DIR
    DOC_STORE_PATH: Path = STORAGE_DIR / "docstore.json"
    MEMORY_STORE_PATH: Path = STORAGE_DIR / "memories.json"
    VECTOR_STORE_PATH: Path = STORAGE_DIR / "vector_store.json"

    @property
    def OFFLINE_TEST_MODE(self) -> bool:
        return os.getenv("OFFLINE_TEST_MODE", "false").lower() in ("true", "1", "yes")


settings = Settings()
