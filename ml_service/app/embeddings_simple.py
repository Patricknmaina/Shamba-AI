"""
Simple embeddings using OpenAI's embedding API.
This avoids the need for sentence-transformers and complex build dependencies.
"""

import os
from typing import List
import numpy as np
from openai import OpenAI


class EmbeddingService:
    """Embedding service using OpenAI's embedding API."""

    def __init__(self, model_name: str = "text-embedding-3-small"):
        """
        Initialize OpenAI embedding service.

        Args:
            model_name: OpenAI embedding model to use
                       text-embedding-3-small: 1536 dim, $0.02/1M tokens (recommended)
                       text-embedding-3-large: 3072 dim, $0.13/1M tokens
                       text-embedding-ada-002: 1536 dim, $0.10/1M tokens (legacy)
        """
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        self.client = OpenAI(api_key=api_key)
        self.model_name = model_name
        self.embedding_dim = 1536 if model_name in ["text-embedding-3-small", "text-embedding-ada-002"] else 3072

        print(f"Loading embedding model: {model_name}")

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of texts to embed

        Returns:
            numpy array of shape (len(texts), embedding_dim)
        """
        if not texts:
            return np.array([])

        try:
            # Call OpenAI API
            response = self.client.embeddings.create(
                model=self.model_name,
                input=texts
            )
            
            # Extract embeddings
            embeddings = [item.embedding for item in response.data]
            return np.array(embeddings)

        except Exception as e:
            print(f"Error generating embeddings: {e}")
            raise

    def embed_query(self, query: str) -> np.ndarray:
        """
        Generate embedding for a single query.

        Args:
            query: Query text

        Returns:
            numpy array of shape (embedding_dim,)
        """
        embeddings = self.embed_texts([query])
        return embeddings[0] if len(embeddings) > 0 else np.array([])

    def embed(self, query: str) -> np.ndarray:
        """
        Generate embedding for a single query (alias for embed_query).

        Args:
            query: Query text

        Returns:
            numpy array of shape (embedding_dim,)
        """
        return self.embed_query(query)

    def get_embedding_dim(self) -> int:
        """Get embedding dimension."""
        return self.embedding_dim

    def is_available(self) -> bool:
        """Check if the service is available."""
        try:
            # Test with a simple query
            test_embedding = self.embed_query("test")
            return len(test_embedding) == self.embedding_dim
        except:
            return False


# For backward compatibility
OpenAIEmbeddingService = EmbeddingService