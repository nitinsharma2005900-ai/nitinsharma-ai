from typing import List, Dict, Any, Optional
from app.core.compat import BaseModel, Field


class TelemetryData(BaseModel):
    retrieval_latency_ms: float = Field(..., description="Hybrid search and parent mapping latency in ms")
    rerank_latency_ms: float = Field(..., description="Cohere ReRank and context compression latency in ms")
    generation_latency_ms: float = Field(..., description="LLM generation latency in ms")
    total_latency_ms: float = Field(..., description="Total roundtrip pipeline latency in ms")


class CitationItem(BaseModel):
    document_name: str
    chunk_id: str
    relevance_score: float
    snippet: str


class RetrievedContextItem(BaseModel):
    child_id: Optional[str] = None
    parent_id: str
    document_id: str
    document_name: str
    text: str
    rerank_score: float
    rrf_score: Optional[float] = None


class MemoryInfo(BaseModel):
    user_id: str
    memories_applied: List[str] = Field(default_factory=list)
    new_facts_extracted: List[str] = Field(default_factory=list)


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, description="User question or prompt")
    user_id: str = Field(default="usr_99", description="Unique user identifier for semantic memory")
    session_id: str = Field(default="session_001", description="Session identifier for multi-session chat")


class ChatResponse(BaseModel):
    answer: str
    sources: List[str]
    citations: List[CitationItem]
    retrieved_context: List[RetrievedContextItem]
    memory: MemoryInfo
    telemetry: TelemetryData
