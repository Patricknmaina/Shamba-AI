"""
Simple translation wrapper using OpenAI GPT for translation.
No external translation library needed - uses OpenAI GPT-4o-mini for translation.
This is simpler and avoids build dependency issues.
"""

import os
from typing import Optional, List
from openai import OpenAI


class SimpleTranslationService:
    """Simple translation service using OpenAI GPT."""

    def __init__(self):
        """Initialize translation service."""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("Warning: OPENAI_API_KEY not set. Translation will not work.")
            self.client = None
        else:
            try:
                self.client = OpenAI(api_key=api_key)
                print("OpenAI Translation Service initialized")
            except Exception as e:
                print(f"Error initializing OpenAI: {e}")
                self.client = None

    def translate_text(
        self,
        text: str,
        target_lang: str,
        source_lang: Optional[str] = 'en'
    ) -> str:
        """
        Translate text to target language using OpenAI GPT.

        Args:
            text: Text to translate
            target_lang: Target language code (e.g., 'sw', 'fr', 'es')
            source_lang: Source language code (default: 'en')

        Returns:
            Translated text
        """
        if not text or not text.strip():
            return text

        # If target is same as source, return as-is
        if target_lang == source_lang:
            return text

        # If no client, return original
        if not self.client:
            print(f"No OpenAI client available. Returning original text.")
            return text

        # Language code to full name mapping
        lang_names = {
            'en': 'English',
            'sw': 'Swahili',
            'fr': 'French',
            'es': 'Spanish',
            'pt': 'Portuguese',
            'ar': 'Arabic',
            'de': 'German',
            'it': 'Italian',
        }

        source_name = lang_names.get(source_lang, source_lang)
        target_name = lang_names.get(target_lang, target_lang)

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a professional translator. Translate the following text from {source_name} to {target_name}. Provide ONLY the translation, no explanations or additional text."
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                temperature=0.3,
                max_tokens=2000
            )

            translated = response.choices[0].message.content.strip()
            return translated

        except Exception as e:
            print(f"Translation error ({source_lang} → {target_lang}): {e}")
            return text  # Return original text on error

    def translate_to_english(self, text: str, source_lang: Optional[str] = None) -> str:
        """
        Translate text to English.

        Args:
            text: Text to translate
            source_lang: Source language (optional)

        Returns:
            Text in English
        """
        if not source_lang:
            # Simple language detection
            source_lang = self._detect_simple_language(text)

        if source_lang == 'en':
            return text

        return self.translate_text(text, target_lang='en', source_lang=source_lang)

    def _detect_simple_language(self, text: str) -> str:
        """
        Simple language detection based on common words.
        """
        text_lower = text.lower()

        # Swahili common words
        swahili_words = ['ninaweza', 'habari', 'mambo', 'nini', 'kwa', 'ya', 'na', 'si', 'ni']
        if any(word in text_lower for word in swahili_words):
            return 'sw'

        # French common words
        french_words = ['comment', 'bonjour', 'merci', 'pour', 'dans', 'avec', 'est', 'que']
        if any(word in text_lower for word in french_words):
            return 'fr'

        # Spanish common words
        spanish_words = ['cómo', 'hola', 'gracias', 'para', 'con', 'que', 'es', 'como']
        if any(word in text_lower for word in spanish_words):
            return 'es'

        # Default to English
        return 'en'

    def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes."""
        return ['en', 'sw', 'fr', 'es', 'pt', 'ar', 'de', 'it']

    def is_available(self) -> bool:
        """Check if translation service is available."""
        return self.client is not None