"""
Utility functions for text processing, chunking, and embeddings.
"""

import re
from typing import List, Dict, Tuple, Any
import numpy as np


def chunk_text(
    text: str,
    chunk_size: int = 500,
    overlap: int = 75,
    min_chunk_size: int = 100
) -> List[Dict[str, Any]]:
    """
    Split text into overlapping chunks based on word count.

    Args:
        text: Input text to chunk
        chunk_size: Target number of words per chunk
        overlap: Number of words to overlap between chunks
        min_chunk_size: Minimum chunk size in words

    Returns:
        List of chunk dictionaries with text, start_char, end_char, word_count
    """
    if not text or not text.strip():
        return []

    # Split into words while keeping track of positions
    words = text.split()

    if len(words) < min_chunk_size:
        # Text too short, return as single chunk
        return [{
            'text': text,
            'start_char': 0,
            'end_char': len(text),
            'word_count': len(words),
            'chunk_id': 0
        }]

    chunks = []
    chunk_id = 0
    start_idx = 0

    while start_idx < len(words):
        # Get chunk words
        end_idx = min(start_idx + chunk_size, len(words))
        chunk_words = words[start_idx:end_idx]

        # Find character positions
        # Calculate by reconstructing text up to this point
        start_text = ' '.join(words[:start_idx])
        start_char = len(start_text) + (1 if start_idx > 0 else 0)

        chunk_text = ' '.join(chunk_words)
        end_char = start_char + len(chunk_text)

        chunks.append({
            'text': chunk_text,
            'start_char': start_char,
            'end_char': end_char,
            'word_count': len(chunk_words),
            'chunk_id': chunk_id
        })

        chunk_id += 1

        # Move to next chunk with overlap
        if end_idx >= len(words):
            break
        start_idx += chunk_size - overlap

    return chunks


def normalize_vector(vector: np.ndarray) -> np.ndarray:
    """Normalize a vector to unit length for cosine similarity."""
    norm = np.linalg.norm(vector)
    if norm == 0:
        return vector
    return vector / norm


def extract_sentences(text: str, max_sentences: int = 3) -> str:
    """Extract first N sentences from text."""
    # Simple sentence splitter
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    return '. '.join(sentences[:max_sentences]) + '.'


def clean_markdown_text(md_text: str) -> str:
    """Clean markdown text for processing."""
    # Remove markdown headers markers but keep text
    text = re.sub(r'^#+\s+', '', md_text, flags=re.MULTILINE)

    # Remove horizontal rules
    text = re.sub(r'^[-*_]{3,}$', '', text, flags=re.MULTILINE)

    # Remove extra whitespace
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)

    return text.strip()


def prepare_rag_context(chunks: List[Dict[str, Any]], max_chars: int = 3000) -> str:
    """
    Prepare context from retrieved chunks for RAG prompting.

    Args:
        chunks: List of chunk dictionaries with 'text' and metadata
        max_chars: Maximum characters to include

    Returns:
        Formatted context string
    """
    context_parts = []
    total_chars = 0

    for i, chunk in enumerate(chunks, 1):
        chunk_text = chunk.get('text', '')
        title = chunk.get('title', 'Unknown Document')

        # Format chunk with source
        formatted = f"[Source {i}: {title}]\n{chunk_text}\n"

        if total_chars + len(formatted) > max_chars:
            break

        context_parts.append(formatted)
        total_chars += len(formatted)

    return '\n'.join(context_parts)


def build_rag_prompt(question: str, context: str) -> str:
    """
    Build RAG prompt for Claude with grounding instructions.

    Args:
        question: User's question
        context: Retrieved context passages

    Returns:
        Formatted prompt string
    """
    prompt = f"""You are an experienced agronomy advisor helping smallholder farmers in East Africa.

Use ONLY the passages below to answer the question. If the passages don't contain enough information to answer confidently, say "I don't have enough specific information in my knowledge base about this topic."

Cite sources in brackets like [Source 1] when referencing information.

Provide:
1. A concise explanation (3-5 sentences)
2. EXACTLY TWO practical actions the farmer can take

Be specific, practical, and use simple language suitable for smallholder farmers.

PASSAGES:
{context}

QUESTION: {question}

ANSWER:"""

    return prompt


def format_sources(chunks: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Format retrieved chunks as source references.

    Args:
        chunks: List of chunk dictionaries

    Returns:
        List of formatted source dictionaries
    """
    sources = []

    for i, chunk in enumerate(chunks, 1):
        source = {
            'title': chunk.get('title', 'Unknown Document'),
            'snippet': extract_sentences(chunk.get('text', ''), max_sentences=2),
            'url': chunk.get('source_url', ''),
            'page': chunk.get('page', ''),
        }
        sources.append(source)

    return sources