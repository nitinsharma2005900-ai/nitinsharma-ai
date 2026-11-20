from app.core.compat import APIRouter, HTTPException, status

from app.schemas.memory import (
    UserMemoriesResponse,
    ClearMemoryRequest,
    ClearMemoryResponse,
)
from app.rag.pipeline import rag_pipeline

router = APIRouter()


@router.get(
    "/users/{user_id}/memories",
    response_model=UserMemoriesResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve semantic memories for user",
)
def get_user_memories(user_id: str):
    memories = rag_pipeline.memory_store.get_user_memories(user_id)
    return UserMemoriesResponse(
        user_id=user_id,
        total_memories=len(memories),
        memories=memories,
    )


@router.post(
    "/memory/clear",
    response_model=ClearMemoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Clear semantic memory for user",
)
def clear_memory(payload: ClearMemoryRequest):
    cleared = rag_pipeline.memory_store.clear_user_memories(payload.user_id)
    return ClearMemoryResponse(
        status="success",
        message=f"Cleared {cleared} memory items for user '{payload.user_id}'.",
        cleared_count=cleared,
        user_id=payload.user_id,
    )


@router.delete(
    "/users/{user_id}/memories/{memory_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a single memory fact",
)
def delete_single_memory(user_id: str, memory_id: str):
    success = rag_pipeline.memory_store.delete_memory(user_id, memory_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Memory item '{memory_id}' not found for user '{user_id}'.",
        )
    return {"status": "success", "message": f"Memory '{memory_id}' deleted."}
