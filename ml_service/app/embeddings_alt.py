"""
Alternative embeddings using sentence-transformers (for MVP).
Since Claude embeddings API is not publicly available, we use sentence-transformers.
"""

import os
from typing import List
import numpy as np
from anthropic import Anthropic

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print("Warning: sentence-transformers not installed. Install with: pip install sentence-transformers")


class EmbeddingService:
    """Embedding service using sentence-transformers."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize embedding service.

        Args:
            model_name: Name of sentence-transformer model to use
                       all-MiniLM-L6-v2: Fast, 384 dim (recommended for MVP)
                       all-mpnet-base-v2: Better quality, 768 dim
        """
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "sentence-transformers not installed. "
                "Install with: pip install sentence-transformers"
            )

        print(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        print(f"Model loaded. Embedding dimension: {self.embedding_dim}")

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

        embedding = self.model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
        return embedding

    def embed_batch(self, texts: List[str], batch_size: int = 32, show_progress: bool = True) -> np.ndarray:
        """
        Get embeddings for multiple texts.

        Args:
            texts: List of text strings
            batch_size: Batch size for encoding
            show_progress: Show progress bar

        Returns:
            2D numpy array of embeddings (num_texts x embedding_dim)
        """
        if not texts:
            return np.array([])

        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True,
            normalize_embeddings=True
        )

        return embeddings


def get_anthropic_client():
    """Get Anthropic client for text generation."""
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")
    return Anthropic(api_key=api_key)


def generate_answer(prompt: str, max_tokens: int = 1024) -> str:
    """
    Generate answer using Claude.

    Args:
        prompt: Input prompt with context and question
        max_tokens: Maximum tokens to generate

    Returns:
        Generated answer text
    """
    client = get_anthropic_client()

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=max_tokens,
        temperature=0.3,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    # Extract text from response
    answer = response.content[0].text

    return answer