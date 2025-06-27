#!/usr/bin/env python3
"""
Modular Translation Addition Tool for Web Sherlock
Allows easy addition of new languages and translation keys
"""

import json
import os
import sys
from typing import Dict, Optional

def add_new_language(language_code: str, base_language: str = 'en') -> bool:
    """Create a new language file based on an existing one"""
    translations_dir = 'translations'
    base_file = os.path.join(translations_dir, f'{base_language}.json')
    new_file = os.path.join(translations_dir, f'{language_code}.json')
    
    if not os.path.exists(base_file):
        print(f"Error: Base language file {base_file} not found")
        return False
    
    if os.path.exists(new_file):
        print(f"Warning: Language file {new_file} already exists")
        return False
    
    try:
        # Load base language
        with open(base_file, 'r', encoding='utf-8') as f:
            base_translations = json.load(f)
        
        # Create new language file with placeholder translations
        new_translations = {}
        for key, value in base_translations.items():
            new_translations[key] = f"[{language_code.upper()}] {value}"
        
        # Save new language file
        with open(new_file, 'w', encoding='utf-8') as f:
            json.dump(new_translations, f, indent=2, ensure_ascii=False)
        
        print(f"Successfully created {new_file}")
        print(f"Please edit the file to add proper translations for language: {language_code}")
        return True
        
    except Exception as e:
        print(f"Error creating new language file: {e}")
        return False

def add_translation_key(key: str, translations: Dict[str, str]) -> bool:
    """Add a new translation key to all existing language files"""
    translations_dir = 'translations'
    
    if not os.path.exists(translations_dir):
        print(f"Error: Translations directory {translations_dir} not found")
        return False
    
    # Get all language files
    language_files = []
    for filename in os.listdir(translations_dir):
        if filename.endswith('.json') and not filename.startswith('_'):
            language_files.append(filename)
    
    if not language_files:
        print("Error: No language files found")
        return False
    
    success_count = 0
    
    for filename in language_files:
        lang_code = filename[:-5]  # Remove .json
        filepath = os.path.join(translations_dir, filename)
        
        try:
            # Load existing translations
            with open(filepath, 'r', encoding='utf-8') as f:
                existing_translations = json.load(f)
            
            # Add new key if translation provided for this language
            if lang_code in translations:
                existing_translations[key] = translations[lang_code]
                
                # Save updated translations
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(existing_translations, f, indent=2, ensure_ascii=False)
                
                print(f"Added key '{key}' to {lang_code}")
                success_count += 1
            else:
                print(f"Warning: No translation provided for language '{lang_code}'")
        
        except Exception as e:
            print(f"Error updating {filepath}: {e}")
    
    return success_count > 0

def update_translation_key(key: str, translations: Dict[str, str]) -> bool:
    """Update an existing translation key in all language files"""
    translations_dir = 'translations'
    
    if not os.path.exists(translations_dir):
        print(f"Error: Translations directory {translations_dir} not found")
        return False
    
    # Get all language files
    language_files = []
    for filename in os.listdir(translations_dir):
        if filename.endswith('.json') and not filename.startswith('_'):
            language_files.append(filename)
    
    if not language_files:
        print("Error: No language files found")
        return False
    
    success_count = 0
    
    for filename in language_files:
        lang_code = filename[:-5]  # Remove .json
        filepath = os.path.join(translations_dir, filename)
        
        try:
            # Load existing translations
            with open(filepath, 'r', encoding='utf-8') as f:
                existing_translations = json.load(f)
            
            # Update key if translation provided for this language
            if lang_code in translations:
                if key in existing_translations:
                    existing_translations[key] = translations[lang_code]
                    
                    # Save updated translations
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(existing_translations, f, indent=2, ensure_ascii=False)
                    
                    print(f"Updated key '{key}' in {lang_code}")
                    success_count += 1
                else:
                    print(f"Warning: Key '{key}' not found in {lang_code}")
            else:
                print(f"Warning: No translation provided for language '{lang_code}'")
        
        except Exception as e:
            print(f"Error updating {filepath}: {e}")
    
    return success_count > 0

def list_missing_keys() -> None:
    """List keys that are missing from language files"""
    translations_dir = 'translations'
    
    if not os.path.exists(translations_dir):
        print(f"Error: Translations directory {translations_dir} not found")
        return
    
    # Get all language files
    language_files = []
    all_translations = {}
    
    for filename in os.listdir(translations_dir):
        if filename.endswith('.json') and not filename.startswith('_'):
            lang_code = filename[:-5]
            filepath = os.path.join(translations_dir, filename)
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    all_translations[lang_code] = json.load(f)
                language_files.append(lang_code)
            except Exception as e:
                print(f"Error loading {filepath}: {e}")
    
    if not language_files:
        print("No language files found")
        return
    
    # Find all unique keys
    all_keys = set()
    for translations in all_translations.values():
        all_keys.update(translations.keys())
    
    # Check for missing keys
    missing_keys = {}
    for lang_code in language_files:
        lang_keys = set(all_translations[lang_code].keys())
        missing = all_keys - lang_keys
        if missing:
            missing_keys[lang_code] = missing
    
    if missing_keys:
        print("Missing translation keys:")
        for lang_code, keys in missing_keys.items():
            print(f"\n{lang_code}:")
            for key in sorted(keys):
                print(f"  - {key}")
    else:
        print("All languages have the same translation keys")

def interactive_mode():
    """Interactive mode for adding translations"""
    print("Web Sherlock Translation Manager")
    print("================================")
    
    while True:
        print("\nOptions:")
        print("1. Add new language")
        print("2. Add new translation key")
        print("3. Update existing translation key")
        print("4. List missing keys")
        print("5. Exit")
        
        choice = input("\nSelect option (1-5): ").strip()
        
        if choice == '1':
            lang_code = input("Enter new language code (e.g., 'es', 'fr', 'de'): ").strip().lower()
            base_lang = input("Base language to copy from (default: en): ").strip().lower() or 'en'
            add_new_language(lang_code, base_lang)
        
        elif choice == '2':
            key = input("Enter translation key: ").strip()
            if not key:
                print("Error: Key cannot be empty")
                continue
            
            translations = {}
            print("Enter translations for each language (press Enter to skip):")
            
            # Get available languages
            translations_dir = 'translations'
            for filename in os.listdir(translations_dir):
                if filename.endswith('.json'):
                    lang_code = filename[:-5]
                    translation = input(f"{lang_code}: ").strip()
                    if translation:
                        translations[lang_code] = translation
            
            if translations:
                add_translation_key(key, translations)
            else:
                print("No translations provided")
        
        elif choice == '3':
            key = input("Enter translation key to update: ").strip()
            if not key:
                print("Error: Key cannot be empty")
                continue
            
            translations = {}
            print("Enter new translations for each language (press Enter to skip):")
            
            # Get available languages
            translations_dir = 'translations'
            for filename in os.listdir(translations_dir):
                if filename.endswith('.json'):
                    lang_code = filename[:-5]
                    translation = input(f"{lang_code}: ").strip()
                    if translation:
                        translations[lang_code] = translation
            
            if translations:
                update_translation_key(key, translations)
            else:
                print("No translations provided")
        
        elif choice == '4':
            list_missing_keys()
        
        elif choice == '5':
            print("Goodbye!")
            break
        
        else:
            print("Invalid option")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == 'add-lang':
            if len(sys.argv) >= 3:
                lang_code = sys.argv[2]
                base_lang = sys.argv[3] if len(sys.argv) >= 4 else 'en'
                add_new_language(lang_code, base_lang)
            else:
                print("Usage: python add_translation.py add-lang <language_code> [base_language]")
        
        elif sys.argv[1] == 'check':
            list_missing_keys()
        
        else:
            print("Usage:")
            print("  python add_translation.py                    # Interactive mode")
            print("  python add_translation.py add-lang <code>    # Add new language")
            print("  python add_translation.py check              # Check missing keys")
    else:
        interactive_mode()