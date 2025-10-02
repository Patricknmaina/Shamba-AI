"""
OpenAI GPT integration for text generation.
"""

import os
from typing import Optional
from openai import OpenAI


def get_openai_client():
    """Get OpenAI client with API key from environment."""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    return OpenAI(api_key=api_key)


def generate_answer(
    prompt: str,
    max_tokens: int = 1024,
    temperature: float = 0.3,
    model: str = "gpt-4o-mini"
) -> str:
    """
    Generate answer using OpenAI GPT-4o-mini.

    Args:
        prompt: Input prompt with context and question
        max_tokens: Maximum tokens to generate
        temperature: Temperature for generation (0.0-2.0)
        model: Model to use (default: gpt-4o-mini)

    Returns:
        Generated answer text
    """
    client = get_openai_client()

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are an experienced agricultural advisor specializing in smallholder farming in East Africa. Provide practical, actionable advice based only on the provided information."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        max_tokens=max_tokens,
        temperature=temperature
    )

    # Extract answer from response
    answer = response.choices[0].message.content

    return answer


def generate_with_system_prompt(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 1024,
    temperature: float = 0.3,
    model: str = "gpt-4o-mini"
) -> str:
    """
    Generate text with custom system and user prompts.

    Args:
        system_prompt: System instructions
        user_prompt: User query/prompt
        max_tokens: Maximum tokens to generate
        temperature: Temperature for generation
        model: Model to use

    Returns:
        Generated text
    """
    client = get_openai_client()

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=max_tokens,
        temperature=temperature
    )

    return response.choices[0].message.content