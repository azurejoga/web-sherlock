"""
Modular Translation System for Web Sherlock
Supports easy addition of new languages and dynamic loading
"""

import json
import os
from typing import Dict, List, Optional


class TranslationManager:
    def __init__(self, translations_dir='translations'):
        self.translations_dir = translations_dir
        self._translations_cache = {}
        self.default_language = 'en'
        self.supported_languages = self._discover_languages()
    
    def _discover_languages(self) -> List[str]:
        """Automatically discover available language files"""
        languages = []
        if os.path.exists(self.translations_dir):
            for filename in os.listdir(self.translations_dir):
                if filename.endswith('.json') and not filename.startswith('_'):
                    lang_code = filename[:-5]  # Remove .json extension
                    languages.append(lang_code)
        return sorted(languages)
    
    def _load_language(self, language: str) -> Dict[str, str]:
        """Load translations for a specific language"""
        if language in self._translations_cache:
            return self._translations_cache[language]
        
        language_file = os.path.join(self.translations_dir, f"{language}.json")
        
        if not os.path.exists(language_file):
            # Fallback to default language
            if language != self.default_language:
                return self._load_language(self.default_language)
            else:
                # Return empty dict if even default language is missing
                return {}
        
        try:
            with open(language_file, 'r', encoding='utf-8') as f:
                translations = json.load(f)
                self._translations_cache[language] = translations
                return translations
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading translations for {language}: {e}")
            if language != self.default_language:
                return self._load_language(self.default_language)
            return {}
    
    def get_translations(self, language: Optional[str] = None) -> Dict[str, str]:
        """Get translations for specified language"""
        if language is None:
            language = self.default_language
        
        if language not in self.supported_languages:
            language = self.default_language
        
        return self._load_language(language)
    
    def get_translation(self, key: str, language: Optional[str] = None, fallback: Optional[str] = None) -> str:
        """Get a specific translation"""
        lang = language if language is not None else self.default_language
        translations = self.get_translations(lang)
        return translations.get(key, fallback or key)
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes"""
        return self.supported_languages
    
    def add_language(self, language_code: str, translations: Dict[str, str]) -> bool:
        """Add a new language"""
        try:
            language_file = os.path.join(self.translations_dir, f"{language_code}.json")
            os.makedirs(self.translations_dir, exist_ok=True)
            
            with open(language_file, 'w', encoding='utf-8') as f:
                json.dump(translations, f, indent=2, ensure_ascii=False)
            
            # Update cache and supported languages
            self._translations_cache[language_code] = translations
            if language_code not in self.supported_languages:
                self.supported_languages.append(language_code)
                self.supported_languages.sort()
            
            return True
        except Exception as e:
            print(f"Error adding language {language_code}: {e}")
            return False
    
    def update_translation(self, language_code: str, key: str, value: str) -> bool:
        """Update a specific translation"""
        try:
            translations = self.get_translations(language_code).copy()
            translations[key] = value
            return self.add_language(language_code, translations)
        except Exception as e:
            print(f"Error updating translation {key} for {language_code}: {e}")
            return False
    
    def reload_translations(self):
        """Reload all translations from disk"""
        self._translations_cache.clear()
        self.supported_languages = self._discover_languages()


# Global translation manager instance
translation_manager = TranslationManager()

# Convenience functions for backward compatibility
def get_translations(language='en'):
    """Get translations for specified language"""
    return translation_manager.get_translations(language)

def get_supported_languages():
    """Get list of supported language codes"""
    return translation_manager.get_supported_languages()

def get_translation(key, language='en', fallback=None):
    """Get a specific translation"""
    return translation_manager.get_translation(key, language, fallback or key)

def add_language(language_code, translations):
    """Add a new language"""
    return translation_manager.add_language(language_code, translations)