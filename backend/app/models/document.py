from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import uuid
import time


@dataclass
class ChildChunk:
    child_id: str
    parent_id: str
    document_id: str
    document_name: str
    text: str
    chunk_index: int
    char_start: int
    char_end: int
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ParentChunk:
    parent_id: str
    document_id: str
    document_name: str
    text: str
    chunk_index: int
    child_ids: List[str] = field(default_factory=list)
    char_start: int = 0
    char_end: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentRecord:
    document_id: str
    filename: str
    file_type: str
    file_size_bytes: int
    char_count: int
    parent_chunks: List[ParentChunk] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)


@dataclass
class ScoredChunk:
    chunk: ChildChunk
    score: float
    rank: int = 0
    retrieval_type: str = "dense"  # "dense" or "sparse"


@dataclass
class FusionResult:
    child_chunk: ChildChunk
    rrf_score: float
    dense_rank: Optional[int] = None
    sparse_rank: Optional[int] = None
    dense_score: Optional[float] = None
    sparse_score: Optional[float] = None


@dataclass
class RerankedDocument:
    parent_chunk: ParentChunk
    matched_child: Optional[ChildChunk]
    relevance_score: float
    compressed_text: str
    rrf_score: float = 0.0
