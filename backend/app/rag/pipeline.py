import re
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

from app.core.config import settings
from app.core.telemetry import TelemetryTimer
from app.models.document import ChildChunk, ParentChunk, FusionResult, RerankedDocument
from app.services.document_service import DocumentService
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.vector_store import VectorStore
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.parent_retriever import ParentDocumentRetriever
from app.rag.compressor import CohereReRankCompressor
from app.memory.semantic_memory import SemanticMemoryStore
from app.rag.generator import GeminiGenerator
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    TelemetryData,
    CitationItem,
    RetrievedContextItem,
    MemoryInfo,
)

SUMMARY_REQUEST_PATTERN = re.compile(
    r"\b(?:summar(?:y|ize|ise|izing|ising)|main\s+points?|key\s+points?|"
    r"important\s+points?|overview|takeaways|gist|saaransh|mukhya\s+baatein|"
    r"(?:describe|explain)\s+(?:(?:the|this|uploaded|attached)\s+)?"
    r"(?:documents?|pdfs?|files?)|"
    r"what\s+is\s+(?:(?:the|this|uploaded|attached)\s+)?"
    r"(?:documents?|pdfs?|files?)\s+about|"
    r"tell\s+me\s+about\s+(?:(?:the|this|uploaded|attached)\s+)?"
    r"(?:documents?|pdfs?|files?))\b",
    re.IGNORECASE,
)


class RAGPipeline:
    """
    End-to-end Advanced RAG Agent pipeline integrating:
    - Hybrid Dense + Sparse Search (BM25 + Cohere/Local Vectors)
    - Reciprocal Rank Fusion (RRF)
    - Parent Document Retrieval
    - Cohere ReRank & Context Compression
    - Mem0 Semantic Memory & Persona Adaptation
    - Google Gemini Faithful Generation with Citations
    - Real-time Latency Telemetry Tracking
    """

    def __init__(self):
        self.doc_service = DocumentService()
        self.vector_store = VectorStore()
        self.bm25_retriever = BM25Retriever()
        self.parent_retriever = ParentDocumentRetriever(self.doc_service)
        self.compressor = CohereReRankCompressor(
            model=settings.COHERE_RERANK_MODEL,
            top_n=settings.TOP_N_RERANK,
            threshold=settings.RELEVANCE_SCORE_THRESHOLD,
        )
        self.memory_store = SemanticMemoryStore()
        self.generator = GeminiGenerator(model=settings.GEMINI_MODEL)

        # Index any existing documents on initialization
        self._sync_retrieval_indices()

    def _document_summary_context(
        self,
        query: str,
    ) -> Optional[List[RerankedDocument]]:
        if not SUMMARY_REQUEST_PATTERN.search(query):
            return None

        documents = self.doc_service.list_documents()
        normalized_query = re.sub(r"[\W_]+", " ", query.casefold())
        named_documents = [
            document
            for document in documents
            if re.sub(r"[\W_]+", " ", Path(document.filename).stem.casefold())
            in normalized_query
        ]

        if len(named_documents) == 1:
            document = named_documents[0]
        elif not named_documents and len(documents) == 1:
            document = documents[0]
        else:
            return None

        if not document.parent_chunks:
            return None

        context = []
        for parent in document.parent_chunks:
            matched_child = None
            for child_id in parent.child_ids:
                matched_child = self.doc_service.get_child_chunk(child_id)
                if matched_child:
                    break

            context.append(
                RerankedDocument(
                    parent_chunk=parent,
                    matched_child=matched_child,
                    relevance_score=1.0,
                    compressed_text=parent.text,
                    rrf_score=0.0,
                )
            )

        return context

    def _sync_retrieval_indices(self):
        """Fit BM25 and sync vector store with all available child chunks."""
        all_children = self.doc_service.get_all_child_chunks()
        if all_children:
            self.bm25_retriever.fit(all_children)
            # Re-index vectors if vector store is empty
            if not self.vector_store.chunks_map:
                self.vector_store.add_chunks(all_children)

    def ingest_document(self, file_path: Path, filename: Optional[str] = None):
        """Ingests a document, creates parent/child chunks, and updates indices."""
        record, child_chunks = self.doc_service.process_and_ingest(file_path, filename=filename)
        
        # Add chunks to vector store
        self.vector_store.add_chunks(child_chunks)

        # Re-fit BM25 index with all child chunks
        all_children = self.doc_service.get_all_child_chunks()
        self.bm25_retriever.fit(all_children)

        return record

    def delete_document(self, document_id: str) -> bool:
        """Deletes document and removes associated vectors and child chunks."""
        success = self.doc_service.delete_document(document_id)
        if success:
            self.vector_store.remove_chunks_for_document(document_id)
            all_children = self.doc_service.get_all_child_chunks()
            self.bm25_retriever.fit(all_children)
        return success

    def execute_chat(
        self,
        query: str,
        user_id: str = "usr_99",
        session_id: str = "session_001",
    ) -> ChatResponse:
        """
        Executes complete RAG pipeline with real latency telemetry.
        """
        timer = TelemetryTimer()

        # Step 1: Memory Fact Extraction (extract facts from current turn)
        new_facts = self.memory_store.extract_and_store(user_id, query)
        stored_memories = [m.fact for m in self.memory_store.get_user_memories(user_id)]
        persona_prompt = self.memory_store.build_persona_prompt(user_id)

        summary_context = self._document_summary_context(query)

        # Step 2: Hybrid Retrieval & Parent Document Retrieval
        fused_candidates: List[FusionResult] = []
        parent_candidates = []
        with timer.measure("retrieval"):
            if not summary_context:
                hybrid = HybridRetriever(
                    vector_store=self.vector_store,
                    bm25_retriever=self.bm25_retriever,
                    k=settings.RRF_K,
                )
                fused_candidates, _ = hybrid.retrieve(query, top_k_candidates=settings.TOP_K_CANDIDATES)
                parent_candidates = self.parent_retriever.retrieve_parents(
                    fused_candidates, max_parents=settings.TOP_K_CANDIDATES
                )

        # Step 3: Cohere ReRank & Context Compression
        reranked_docs: List[RerankedDocument] = []
        with timer.measure("rerank"):
            if summary_context:
                reranked_docs = summary_context
            else:
                reranked_docs = self.compressor.rerank_and_compress(query, parent_candidates)

        # Step 4: Generation with Gemini + Persona Adaptation + Citations
        answer_text: str = ""
        sources: List[str] = []
        citations: List[CitationItem] = []
        with timer.measure("generation"):
            answer_text, sources, citations = self.generator.generate(
                query=query,
                documents=reranked_docs,
                persona_context=persona_prompt,
            )

        # Finalize Telemetry Timings
        timings = timer.finish()

        # Format context items for response inspection
        context_items: List[RetrievedContextItem] = []
        for doc in reranked_docs:
            p = doc.parent_chunk
            c = doc.matched_child
            context_items.append(
                RetrievedContextItem(
                    child_id=c.child_id if c else None,
                    parent_id=p.parent_id,
                    document_id=p.document_id,
                    document_name=p.document_name,
                    text=doc.compressed_text,
                    rerank_score=doc.relevance_score,
                    rrf_score=doc.rrf_score,
                )
            )

        return ChatResponse(
            answer=answer_text,
            sources=sources,
            citations=citations,
            retrieved_context=context_items,
            memory=MemoryInfo(
                user_id=user_id,
                memories_applied=stored_memories,
                new_facts_extracted=new_facts,
            ),
            telemetry=TelemetryData(**timings),
        )


# Global singleton pipeline instance
rag_pipeline = RAGPipeline()
