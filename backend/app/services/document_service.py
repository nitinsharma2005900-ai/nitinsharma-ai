import json
import hashlib
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple

from app.core.config import settings
from app.models.document import ChildChunk, ParentChunk, DocumentRecord
from app.utils.text_parser import extract_text_from_file


class DocumentService:
    """Manages document ingestion, parent-child chunking, and persistent storage."""

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or settings.DOC_STORE_PATH
        self._documents: Dict[str, DocumentRecord] = {}
        self._parent_map: Dict[str, ParentChunk] = {}
        self._child_map: Dict[str, ChildChunk] = {}
        self.load()

    def _chunk_text(
        self,
        text: str,
        chunk_size: int,
        overlap: int,
    ) -> List[Tuple[str, int, int]]:
        """
        Splits text into chunks respecting sentence/word boundaries.
        Returns list of (chunk_text, char_start, char_end).
        """
        if not text:
            return []

        chunks = []
        text_len = len(text)
        start = 0

        while start < text_len:
            end = min(start + chunk_size, text_len)

            # If not at the end of text, attempt to find a natural boundary
            if end < text_len:
                # Look backwards for newline, period, or space
                boundary = -1
                for sep in ("\n\n", "\n", ". ", "? ", "! ", " "):
                    pos = text.rfind(sep, start + chunk_size // 2, end)
                    if pos != -1:
                        boundary = pos + len(sep)
                        break
                if boundary != -1:
                    end = boundary

            chunk_str = text[start:end].strip()
            if chunk_str:
                chunks.append((chunk_str, start, end))

            if end >= text_len:
                break
            # Step forward by (chunk_length - overlap)
            step = max(end - start - overlap, 1)
            start += step

        return chunks

    def process_and_ingest(
        self,
        file_path: Path,
        filename: Optional[str] = None
    ) -> Tuple[DocumentRecord, List[ChildChunk]]:
        """
        Extracts document text, creates parent chunks (~1000 chars) and child chunks (~200 chars),
        and persists them.
        """
        fname = filename or file_path.name
        text, file_type = extract_text_from_file(file_path)

        if not text.strip():
            raise ValueError(f"Document {fname} is empty or contains no extractable text.")

        file_size = file_path.stat().st_size if file_path.exists() else len(text.encode("utf-8"))
        doc_hash = hashlib.md5(f"{fname}_{len(text)}_{time.time()}".encode("utf-8")).hexdigest()[:10]
        doc_id = f"doc_{doc_hash}"

        # 1. Split into Parent chunks (~1000 characters)
        raw_parents = self._chunk_text(
            text,
            chunk_size=settings.PARENT_CHUNK_SIZE,
            overlap=settings.PARENT_CHUNK_OVERLAP,
        )

        parent_chunks: List[ParentChunk] = []
        all_child_chunks: List[ChildChunk] = []

        for p_idx, (p_text, p_start, p_end) in enumerate(raw_parents):
            p_id = f"{doc_id}_p{p_idx:03d}"
            
            # 2. Split Parent into Child chunks (~200 characters)
            raw_children = self._chunk_text(
                p_text,
                chunk_size=settings.CHILD_CHUNK_SIZE,
                overlap=settings.CHILD_CHUNK_OVERLAP,
            )

            child_ids = []
            for c_idx, (c_text, c_rel_start, c_rel_end) in enumerate(raw_children):
                c_id = f"{p_id}_c{c_idx:03d}"
                c_abs_start = p_start + c_rel_start
                c_abs_end = p_start + c_rel_end

                child = ChildChunk(
                    child_id=c_id,
                    parent_id=p_id,
                    document_id=doc_id,
                    document_name=fname,
                    text=c_text,
                    chunk_index=c_idx,
                    char_start=c_abs_start,
                    char_end=c_abs_end,
                    metadata={"source": fname, "parent_id": p_id, "doc_id": doc_id}
                )
                child_ids.append(c_id)
                all_child_chunks.append(child)
                self._child_map[c_id] = child

            parent = ParentChunk(
                parent_id=p_id,
                document_id=doc_id,
                document_name=fname,
                text=p_text,
                chunk_index=p_idx,
                child_ids=child_ids,
                char_start=p_start,
                char_end=p_end,
                metadata={"source": fname, "doc_id": doc_id}
            )
            parent_chunks.append(parent)
            self._parent_map[p_id] = parent

        record = DocumentRecord(
            document_id=doc_id,
            filename=fname,
            file_type=file_type,
            file_size_bytes=file_size,
            char_count=len(text),
            parent_chunks=parent_chunks,
            created_at=time.time(),
        )

        self._documents[doc_id] = record
        self.save()

        return record, all_child_chunks

    def get_parent_chunk(self, parent_id: str) -> Optional[ParentChunk]:
        """Lookup parent chunk by ID."""
        return self._parent_map.get(parent_id)

    def get_child_chunk(self, child_id: str) -> Optional[ChildChunk]:
        """Lookup child chunk by ID."""
        return self._child_map.get(child_id)

    def get_all_child_chunks(self) -> List[ChildChunk]:
        """Returns all indexed child chunks."""
        return list(self._child_map.values())

    def get_document(self, document_id: str) -> Optional[DocumentRecord]:
        """Lookup document record by ID."""
        return self._documents.get(document_id)

    def list_documents(self) -> List[DocumentRecord]:
        """Returns all registered document records."""
        return sorted(list(self._documents.values()), key=lambda d: d.created_at, reverse=True)

    def delete_document(self, document_id: str) -> bool:
        """Deletes a document and its parent and child chunks."""
        if document_id not in self._documents:
            return False

        doc = self._documents.pop(document_id)
        for parent in doc.parent_chunks:
            self._parent_map.pop(parent.parent_id, None)
            for c_id in parent.child_ids:
                self._child_map.pop(c_id, None)

        self.save()
        return True

    def save(self):
        """Persists document registry to JSON file."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "documents": [
                {
                    "document_id": doc.document_id,
                    "filename": doc.filename,
                    "file_type": doc.file_type,
                    "file_size_bytes": doc.file_size_bytes,
                    "char_count": doc.char_count,
                    "created_at": doc.created_at,
                    "parent_chunks": [
                        {
                            "parent_id": p.parent_id,
                            "document_id": p.document_id,
                            "document_name": p.document_name,
                            "text": p.text,
                            "chunk_index": p.chunk_index,
                            "child_ids": p.child_ids,
                            "char_start": p.char_start,
                            "char_end": p.char_end,
                            "metadata": p.metadata,
                        }
                        for p in doc.parent_chunks
                    ],
                }
                for doc in self._documents.values()
            ],
            "children": [
                {
                    "child_id": c.child_id,
                    "parent_id": c.parent_id,
                    "document_id": c.document_id,
                    "document_name": c.document_name,
                    "text": c.text,
                    "chunk_index": c.chunk_index,
                    "char_start": c.char_start,
                    "char_end": c.char_end,
                    "metadata": c.metadata,
                }
                for c in self._child_map.values()
            ]
        }
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load(self):
        """Loads document registry from JSON file if present."""
        if not self.storage_path.exists():
            return

        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self._documents.clear()
            self._parent_map.clear()
            self._child_map.clear()

            # Load children first
            for c_dict in data.get("children", []):
                child = ChildChunk(
                    child_id=c_dict["child_id"],
                    parent_id=c_dict["parent_id"],
                    document_id=c_dict["document_id"],
                    document_name=c_dict["document_name"],
                    text=c_dict["text"],
                    chunk_index=c_dict["chunk_index"],
                    char_start=c_dict["char_start"],
                    char_end=c_dict["char_end"],
                    metadata=c_dict.get("metadata", {}),
                )
                self._child_map[child.child_id] = child

            # Load parent chunks and documents
            for d_dict in data.get("documents", []):
                parents = []
                for p_dict in d_dict.get("parent_chunks", []):
                    parent = ParentChunk(
                        parent_id=p_dict["parent_id"],
                        document_id=p_dict["document_id"],
                        document_name=p_dict["document_name"],
                        text=p_dict["text"],
                        chunk_index=p_dict["chunk_index"],
                        child_ids=p_dict.get("child_ids", []),
                        char_start=p_dict.get("char_start", 0),
                        char_end=p_dict.get("char_end", 0),
                        metadata=p_dict.get("metadata", {}),
                    )
                    parents.append(parent)
                    self._parent_map[parent.parent_id] = parent

                doc = DocumentRecord(
                    document_id=d_dict["document_id"],
                    filename=d_dict["filename"],
                    file_type=d_dict["file_type"],
                    file_size_bytes=d_dict["file_size_bytes"],
                    char_count=d_dict["char_count"],
                    parent_chunks=parents,
                    created_at=d_dict.get("created_at", time.time()),
                )
                self._documents[doc.document_id] = doc

        except Exception as e:
            # If load fails, start fresh
            print(f"Warning: Failed to load docstore: {e}")
