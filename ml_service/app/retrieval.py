"""
RAG retrieval service using FAISS index.
"""

import json
from pathlib import Path
from typing import List, Dict, Any
import numpy as np
import faiss

try:
    from .embeddings_simple import EmbeddingService
    print("Using OpenAI embeddings (simple)")
except ImportError:
    from .embeddings_alt import EmbeddingService
    print("Using sentence-transformers embeddings")


class RetrievalService:
    """RAG retrieval service using FAISS index."""

    def __init__(self, data_dir: str):
        """
        Initialize retrieval service.

        Args:
            data_dir: Directory containing FAISS index and metadata
        """
        self.data_dir = Path(data_dir)
        self.index = None
        self.chunks_metadata = []
        self.embedding_service = None
        self.embedding_dim = None

        self._load_index()

    def _load_index(self):
        """Load FAISS index and metadata."""
        # Load FAISS index
        index_path = self.data_dir / 'faiss.index'
        if not index_path.exists():
            raise FileNotFoundError(f"FAISS index not found at {index_path}")

        self.index = faiss.read_index(str(index_path))
        print(f"Loaded FAISS index with {self.index.ntotal} vectors")

        # Load chunk metadata
        metadata_path = self.data_dir / 'chunks_metadata.json'
        if not metadata_path.exists():
            raise FileNotFoundError(f"Chunk metadata not found at {metadata_path}")

        with open(metadata_path, 'r', encoding='utf-8') as f:
            self.chunks_metadata = json.load(f)

        print(f"Loaded metadata for {len(self.chunks_metadata)} chunks")

        # Initialize embedding service
        try:
            # Try OpenAI embeddings first (simpler, no build deps)
            self.embedding_service = EmbeddingService(model_name='text-embedding-3-small')
        except Exception:
            # Fall back to sentence-transformers
            self.embedding_service = EmbeddingService(model_name='all-MiniLM-L6-v2')

        self.embedding_dim = self.embedding_service.embedding_dim

    def retrieve(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieve top-k relevant chunks for query.

        Args:
            query: Search query
            top_k: Number of chunks to retrieve

        Returns:
            List of chunk dictionaries with similarity scores
        """
        if not query or not query.strip():
            return []

        # Generate query embedding
        query_embedding = self.embedding_service.embed(query)
        query_embedding = query_embedding.reshape(1, -1).astype('float32')

        # Search index
        scores, indices = self.index.search(query_embedding, top_k)

        # Get chunk metadata
        results = []
        for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if idx < len(self.chunks_metadata):
                chunk = self.chunks_metadata[idx].copy()
                chunk['similarity_score'] = float(score)
                chunk['rank'] = i + 1
                results.append(chunk)

        return results

    def get_chunk_by_id(self, chunk_global_id: int) -> Dict[str, Any]:
        """Get specific chunk by global ID."""
        for chunk in self.chunks_metadata:
            if chunk['chunk_global_id'] == chunk_global_id:
                return chunk
        return None

    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        return {
            'num_vectors': self.index.ntotal if self.index else 0,
            'num_chunks': len(self.chunks_metadata),
            'embedding_dim': self.embedding_dim,
            'num_documents': len(set(c['doc_id'] for c in self.chunks_metadata))
        }