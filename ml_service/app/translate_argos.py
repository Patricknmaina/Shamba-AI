"""
Argos Translate service wrapper (offline, free translation).
"""

from typing import Dict, Optional, List
import argostranslate.package
import argostranslate.translate


class ArgosTranslationService:
    """Argos Translate service wrapper for offline translation."""

    def __init__(self):
        """Initialize Argos translation service."""
        self.installed_languages = []
        self._initialize_argos()

    def _initialize_argos(self):
        """Initialize Argos Translate packages."""
        try:
            # Update package index
            argostranslate.package.update_package_index()
            available_packages = argostranslate.package.get_available_packages()

            # Get list of installed packages
            installed_packages = argostranslate.package.get_installed_packages()

            if not installed_packages:
                print("No Argos Translate packages installed yet.")
                print("Installing common language packages for East Africa...")

                # Language codes we want to support
                target_languages = [
                    ('en', 'sw'),  # English to Swahili
                    ('sw', 'en'),  # Swahili to English
                    ('en', 'fr'),  # English to French
                    ('fr', 'en'),  # French to English
                    ('en', 'es'),  # English to Spanish
                    ('es', 'en'),  # Spanish to English
                ]

                # Install packages
                for from_lang, to_lang in target_languages:
                    package = None
                    for pkg in available_packages:
                        if pkg.from_code == from_lang and pkg.to_code == to_lang:
                            package = pkg
                            break

                    if package:
                        try:
                            print(f"  Installing {from_lang} → {to_lang}...")
                            argostranslate.package.install_from_path(package.download())
                            print(f"    ✓ Installed {from_lang} → {to_lang}")
                        except Exception as e:
                            print(f"    ✗ Failed to install {from_lang} → {to_lang}: {e}")
                    else:
                        print(f"    ✗ Package not found: {from_lang} → {to_lang}")

            # Get updated installed packages
            installed_packages = argostranslate.package.get_installed_packages()
            self.installed_languages = [
                (pkg.from_code, pkg.to_code) for pkg in installed_packages
            ]

            if installed_packages:
                print(f"Argos Translate initialized with {len(installed_packages)} language pairs")
            else:
                print("Warning: No Argos Translate packages installed. Translation will not work.")

        except Exception as e:
            print(f"Error initializing Argos Translate: {e}")
            self.installed_languages = []

    def translate_text(
        self,
        text: str,
        target_lang: str,
        source_lang: Optional[str] = 'en'
    ) -> str:
        """
        Translate text to target language using Argos.

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

        # If no packages installed, return original
        if not self.installed_languages:
            print(f"No translation packages available. Returning original text.")
            return text

        try:
            # Check if we have this language pair
            if (source_lang, target_lang) not in self.installed_languages:
                print(f"Translation pair {source_lang} → {target_lang} not available")
                return text

            # Perform translation
            translated = argostranslate.translate.translate(text, source_lang, target_lang)
            return translated

        except Exception as e:
            print(f"Translation error ({source_lang} → {target_lang}): {e}")
            return text  # Return original text on error

    def translate_to_english(self, text: str, source_lang: Optional[str] = None) -> str:
        """
        Translate text to English.

        Args:
            text: Text to translate
            source_lang: Source language (optional, defaults to auto-detect)

        Returns:
            Text in English
        """
        if not source_lang:
            # Try to detect language from common patterns
            source_lang = self._detect_simple_language(text)

        if source_lang == 'en':
            return text

        return self.translate_text(text, target_lang='en', source_lang=source_lang)

    def _detect_simple_language(self, text: str) -> str:
        """
        Simple language detection based on common words.
        For production, use langdetect or similar library.
        """
        text_lower = text.lower()

        # Swahili common words
        swahili_words = ['ninaweza', 'habari', 'mambo', 'nini', 'kwa', 'ya', 'na']
        if any(word in text_lower for word in swahili_words):
            return 'sw'

        # French common words
        french_words = ['comment', 'bonjour', 'merci', 'pour', 'dans', 'avec']
        if any(word in text_lower for word in french_words):
            return 'fr'

        # Spanish common words
        spanish_words = ['cómo', 'hola', 'gracias', 'para', 'con', 'que']
        if any(word in text_lower for word in spanish_words):
            return 'es'

        # Default to English
        return 'en'

    def get_supported_languages(self) -> List[tuple]:
        """Get list of supported language pairs."""
        return self.installed_languages

    def is_available(self) -> bool:
        """Check if translation service is available."""
        return len(self.installed_languages) > 0

    def install_language_package(self, from_code: str, to_code: str) -> bool:
        """
        Install a specific language package.

        Args:
            from_code: Source language code
            to_code: Target language code

        Returns:
            True if successful, False otherwise
        """
        try:
            argostranslate.package.update_package_index()
            available_packages = argostranslate.package.get_available_packages()

            package = None
            for pkg in available_packages:
                if pkg.from_code == from_code and pkg.to_code == to_code:
                    package = pkg
                    break

            if package:
                print(f"Installing {from_code} → {to_code}...")
                argostranslate.package.install_from_path(package.download())
                self.installed_languages.append((from_code, to_code))
                print(f"✓ Installed {from_code} → {to_code}")
                return True
            else:
                print(f"Package not found: {from_code} → {to_code}")
                return False

        except Exception as e:
            print(f"Error installing language package: {e}")
            return False