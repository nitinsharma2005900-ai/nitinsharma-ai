from typing import List, Optional
from app.core.compat import BaseModel, Field


class MemoryItem(BaseModel):
    id: str
    user_id: str
    fact: str
    category: str = "preference"
    created_at: str


class UserMemoriesResponse(BaseModel):
    user_id: str
    total_memories: int
    memories: List[MemoryItem]


class ClearMemoryRequest(BaseModel):
    user_id: str


class ClearMemoryResponse(BaseModel):
    status: str
    message: str
    cleared_count: int
    user_id: str
