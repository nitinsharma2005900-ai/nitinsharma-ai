from app.core.compat import APIRouter, status
from app.core.config import settings
from app.rag.pipeline import rag_pipeline

router = APIRouter()


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Health and Readiness Check",
)
async def health_check():
    docs_count = len(rag_pipeline.doc_service.list_documents())
    children_count = len(rag_pipeline.doc_service.get_all_child_chunks())

    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "mode": "offline_test" if settings.OFFLINE_TEST_MODE else "production",
        "configuration": {
            "gemini_api_configured": bool(settings.GEMINI_API_KEY),
            "cohere_api_configured": bool(settings.COHERE_API_KEY),
            "mem0_api_configured": bool(settings.MEM0_API_KEY),
            "qdrant_configured": bool(settings.QDRANT_URL),
        },
        "stats": {
            "total_documents": docs_count,
            "total_indexed_child_chunks": children_count,
            "parent_chunk_size": settings.PARENT_CHUNK_SIZE,
            "child_chunk_size": settings.CHILD_CHUNK_SIZE,
            "rrf_k": settings.RRF_K,
            "top_n_rerank": settings.TOP_N_RERANK,
        },
    }
