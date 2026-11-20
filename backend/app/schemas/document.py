from typing import List, Optional
from app.core.compat import BaseModel, Field


class DocumentMetadata(BaseModel):
    document_id: str
    filename: str
    file_type: str
    file_size_bytes: int
    char_count: int
    parent_chunk_count: int
    child_chunk_count: int
    created_at: str


class DocumentUploadResponse(BaseModel):
    status: str
    message: str
    document: DocumentMetadata


class DocumentListResponse(BaseModel):
    total: int
    documents: List[DocumentMetadata]


class DocumentDeleteResponse(BaseModel):
    status: str
    message: str
    document_id: str
