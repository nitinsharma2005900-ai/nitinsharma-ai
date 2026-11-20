from app.core.compat import APIRouter, HTTPException, status
from app.schemas.chat import ChatRequest, ChatResponse
from app.rag.pipeline import rag_pipeline

router = APIRouter()


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute Advanced RAG Agent Chat",
    description="Processes query through Hybrid Search, Parent Retrieval, Cohere ReRank, Mem0 Semantic Memory, and Gemini generation with real latency telemetry.",
)
def chat_endpoint(payload: ChatRequest):
    try:
        response = rag_pipeline.execute_chat(
            query=payload.query,
            user_id=payload.user_id,
            session_id=payload.session_id,
        )
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing RAG pipeline: {str(e)}",
        )
