import shutil
from pathlib import Path
from app.core.compat import APIRouter, UploadFile, File, HTTPException, status

from app.core.config import settings
from app.schemas.document import (
    DocumentUploadResponse,
    DocumentListResponse,
    DocumentDeleteResponse,
    DocumentMetadata,
)
from app.rag.pipeline import rag_pipeline

router = APIRouter()


@router.post(
    "/documents/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and ingest PDF, TXT, or DOCX document",
)
def upload_document(file: UploadFile = File(...)):
    filename = file.filename or "unknown"
    suffix = Path(filename).suffix.lower()

    if suffix not in (".pdf", ".txt", ".docx", ".md"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{suffix}'. Allowed: .pdf, .txt, .docx",
        )

    # Save to upload directory
    save_path = settings.UPLOAD_DIR / f"upload_{filename}"
    try:
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Ingest document into pipeline
        record = rag_pipeline.ingest_document(save_path, filename=filename)

        total_children = sum(len(p.child_ids) for p in record.parent_chunks)
        meta = DocumentMetadata(
            document_id=record.document_id,
            filename=record.filename,
            file_type=record.file_type,
            file_size_bytes=record.file_size_bytes,
            char_count=record.char_count,
            parent_chunk_count=len(record.parent_chunks),
            child_chunk_count=total_children,
            created_at=str(record.created_at),
        )

        return DocumentUploadResponse(
            status="success",
            message=f"Successfully ingested '{filename}' with {len(record.parent_chunks)} parent chunks and {total_children} child chunks.",
            document=meta,
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document: {str(e)}",
        )
    finally:
        # Clean up temporary upload file
        if save_path.exists():
            try:
                save_path.unlink()
            except Exception:
                pass


@router.get(
    "/documents",
    response_model=DocumentListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all indexed documents",
)
def list_documents():
    docs = rag_pipeline.doc_service.list_documents()
    items = []
    for doc in docs:
        total_children = sum(len(p.child_ids) for p in doc.parent_chunks)
        items.append(
            DocumentMetadata(
                document_id=doc.document_id,
                filename=doc.filename,
                file_type=doc.file_type,
                file_size_bytes=doc.file_size_bytes,
                char_count=doc.char_count,
                parent_chunk_count=len(doc.parent_chunks),
                child_chunk_count=total_children,
                created_at=str(doc.created_at),
            )
        )
    return DocumentListResponse(total=len(items), documents=items)


@router.delete(
    "/documents/{document_id}",
    response_model=DocumentDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete document from index",
)
def delete_document(document_id: str):
    success = rag_pipeline.delete_document(document_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{document_id}' not found.",
        )
    return DocumentDeleteResponse(
        status="success",
        message=f"Document '{document_id}' and all associated chunks were deleted.",
        document_id=document_id,
    )
