from typing import List, Dict, Optional, Tuple, Set
from app.models.document import ChildChunk, ParentChunk, FusionResult
from app.services.document_service import DocumentService


class ParentDocumentRetriever:
    """
    Retrieves full parent document context for matching child chunks.
    Maintains parent-child mapping and deduplicates parent documents.
    """

    def __init__(self, document_service: DocumentService):
        self.doc_service = document_service

    def retrieve_parents(
        self,
        fused_results: List[FusionResult],
        max_parents: int = 20,
    ) -> List[Tuple[ParentChunk, ChildChunk, float]]:
        """
        Maps child chunks from hybrid search to their parent chunks.
        Deduplicates parent documents, preserving the highest RRF score.
        Returns a list of tuples: (parent_chunk, matched_child_chunk, rrf_score).
        """
        seen_parents: Set[str] = set()
        parent_candidates: List[Tuple[ParentChunk, ChildChunk, float]] = []

        for item in fused_results:
            child = item.child_chunk
            parent_id = child.parent_id

            if parent_id in seen_parents:
                continue

            parent = self.doc_service.get_parent_chunk(parent_id)
            if parent:
                seen_parents.add(parent_id)
                parent_candidates.append((parent, child, item.rrf_score))

            if len(parent_candidates) >= max_parents:
                break

        return parent_candidates
