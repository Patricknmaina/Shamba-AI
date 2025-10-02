"""
Simple embeddings using OpenAI's embedding API.
This avoids the need for sentence-transformers and complex build dependencies.
"""

import os
from typing import List
import numpy as np
from openai import OpenAI


class OpenAIEmbeddingService:
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

        # Set embedding dimension based on model
        if model_name == "text-embedding-3-large":
            self.embedding_dim = 3072
        else:
            self.embedding_dim = 1536

        print(f"OpenAI Embedding Service initialized")
        print(f"Model: {model_name}")
        print(f"Embedding dimension: {self.embedding_dim}")

    def embed(self, text: str) -> np.ndarray:
        """
        Get embedding for single text.

        Args:
            text: Input text

        Returns:
            Normalized embedding vector
        """
        if not text or not text.strip():
            return np.zeros(self.embedding_dim)

        try:
            response = self.client.embeddings.create(
                model=self.model_name,
                input=text
            )

            embedding = np.array(response.data[0].embedding)

            # Normalize
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm

            return embedding

        except Exception as e:
            print(f"Error generating embedding: {e}")
            return np.zeros(self.embedding_dim)

    def embed_batch(self, texts: List[str], batch_size: int = 100, show_progress: bool = True) -> np.ndarray:
        """
        Get embeddings for multiple texts.

        Args:
            texts: List of text strings
            batch_size: Batch size for API calls (OpenAI allows up to 2048)
            show_progress: Show progress (prints every batch)

        Returns:
            2D numpy array of embeddings (num_texts x embedding_dim)
        """
        if not texts:
            return np.array([])

        all_embeddings = []
        total_batches = (len(texts) + batch_size - 1) // batch_size

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_num = i // batch_size + 1

            if show_progress:
                print(f"Processing batch {batch_num}/{total_batches} ({len(batch)} texts)...")

            try:
                response = self.client.embeddings.create(
                    model=self.model_name,
                    input=batch
                )

                # Extract embeddings
                batch_embeddings = [np.array(data.embedding) for data in response.data]

                # Normalize
                for j, emb in enumerate(batch_embeddings):
                    norm = np.linalg.norm(emb)
                    if norm > 0:
                        batch_embeddings[j] = emb / norm

                all_embeddings.extend(batch_embeddings)

            except Exception as e:
                print(f"Error processing batch {batch_num}: {e}")
                # Add zero vectors for failed batch
                all_embeddings.extend([np.zeros(self.embedding_dim) for _ in batch])

        return np.array(all_embeddings)


# Alias for backwards compatibility
EmbeddingService = OpenAIEmbeddingService