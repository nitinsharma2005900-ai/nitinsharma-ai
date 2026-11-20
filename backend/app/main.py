import logging
from contextlib import asynccontextmanager
from fastapi import Request
from app.core.compat import FastAPI, CORSMiddleware, JSONResponse, status

from app.core.config import settings
from app.api import chat, documents, memory, health, analytics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rag_agent")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup validation and configuration notice
    logger.info("=================================================================")
    logger.info("Initializing %s (v%s)", settings.PROJECT_NAME, settings.VERSION)
    logger.info("Storage Dir: %s", settings.STORAGE_DIR)
    logger.info("Upload Dir:  %s", settings.UPLOAD_DIR)
    logger.info("Offline Test Mode: %s", settings.OFFLINE_TEST_MODE)
    logger.info(
        "API Keys Present -> Gemini: %s | Cohere: %s | Mem0: %s | Qdrant: %s",
        bool(settings.GEMINI_API_KEY),
        bool(settings.COHERE_API_KEY),
        bool(settings.MEM0_API_KEY),
        bool(settings.QDRANT_URL),
    )
    logger.info("=================================================================")
    yield
    logger.info("Shutting down %s", settings.PROJECT_NAME)


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "Production-grade Advanced RAG Agent featuring Parent-Document Retrieval, "
        "Dense-Sparse Hybrid Search with Reciprocal Rank Fusion (RRF), Cohere ReRank "
        "Context Compression, Mem0 Semantic Memory persona adaptation, and Google Gemini generation."
    ),
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(chat.router, prefix=settings.API_V1_PREFIX, tags=["Chat"])
app.include_router(documents.router, prefix=settings.API_V1_PREFIX, tags=["Documents"])
app.include_router(memory.router, prefix=settings.API_V1_PREFIX, tags=["Semantic Memory"])
app.include_router(health.router, prefix=settings.API_V1_PREFIX, tags=["System Health"])
app.include_router(analytics.router, prefix=settings.API_V1_PREFIX, tags=["Retrieval Analytics"])


@app.get("/", tags=["Root"])
async def root():
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs_url": "/docs",
        "health_check": f"{settings.API_V1_PREFIX}/health",
        "chat_endpoint": f"{settings.API_V1_PREFIX}/chat",
        "documents_endpoint": f"{settings.API_V1_PREFIX}/documents",
        "memories_endpoint": f"{settings.API_V1_PREFIX}/users/usr_99/memories",
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled Exception at %s: %s", request.url.path, str(exc), exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "message": "An internal server error occurred while processing the request.",
            "detail": str(exc),
            "path": request.url.path,
        },
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
