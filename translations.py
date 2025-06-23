"""
Translation module for Web Sherlock application
"""
import json
import os
from typing import Dict, List

def load_translation_file(language: str) -> dict:
    """Load translation file for specified language"""
    translations_dir = os.path.join(os.path.dirname(__file__), 'translations')
    file_path = os.path.join(translations_dir, f'{language}.json')
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        # Fallback to Portuguese if file not found or invalid
        if language != 'pt':
            return load_translation_file('pt')
        else:
            # If even Portuguese fails, return basic translations
            return {
                'app_title': 'Web Sherlock',
                'error_500': 'Erro interno do servidor'
            }

def get_translations(language='pt'):
    """Get translations for specified language"""
    return load_translation_file(language)

def get_supported_languages():
    """Get list of supported language codes based on available JSON files"""
    translations_dir = os.path.join(os.path.dirname(__file__), 'translations')
    
    if not os.path.exists(translations_dir):
        return ['pt', 'en']  # Default fallback
    
    languages = []
    for filename in os.listdir(translations_dir):
        if filename.endswith('.json'):
            lang_code = filename[:-5]  # Remove .json extension
            languages.append(lang_code)
    
    return sorted(languages) if languages else ['pt', 'en']

def get_language_display_names():
    """Get language display names for the UI"""
    return {
        'pt': 'Português',
        'en': 'English'
    }