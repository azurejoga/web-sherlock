"""
History Manager for Web Sherlock
Handles user search history storage and management using JSON files
"""

import json
import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Any


class HistoryManager:
    def __init__(self, history_dir='history'):
        self.history_dir = history_dir
        self._ensure_history_dir()
    
    def _ensure_history_dir(self):
        """Ensure history directory exists"""
        if not os.path.exists(self.history_dir):
            os.makedirs(self.history_dir, exist_ok=True)
    
    def _get_history_file(self, username: str) -> str:
        """Get history file path for user"""
        # Sanitize username for filename
        safe_username = "".join(c for c in username if c.isalnum() or c in '-_').lower()
        return os.path.join(self.history_dir, f"history-{safe_username}.json")
    
    def _load_history(self, username: str) -> Dict:
        """Load user history from file"""
        history_file = self._get_history_file(username)
        
        if not os.path.exists(history_file):
            return {
                'username': username,
                'searches': [],
                'created_at': datetime.utcnow().isoformat(),
                'last_updated': datetime.utcnow().isoformat()
            }
        
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                'username': username,
                'searches': [],
                'created_at': datetime.utcnow().isoformat(),
                'last_updated': datetime.utcnow().isoformat()
            }
    
    def _save_history(self, username: str, data: Dict):
        """Save user history to file"""
        history_file = self._get_history_file(username)
        data['last_updated'] = datetime.utcnow().isoformat()
        
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def add_search(self, username: str, search_data: Dict) -> bool:
        """Add a search to user history - prevents duplicates"""
        try:
            history = self._load_history(username)
            search_id = search_data.get('search_id')
            
            # Check if search already exists - prevent duplicates
            existing_search = None
            for i, search in enumerate(history['searches']):
                if search.get('search_id') == search_id:
                    existing_search = i
                    break
            
            # Create search entry
            search_entry = {
                'search_id': search_id,
                'usernames': search_data.get('usernames', []),
                'options': search_data.get('options', {}),
                'timestamp': datetime.utcnow().isoformat(),
                'status': search_data.get('status', 'running'),
                'results_count': search_data.get('results_count', 0),
                'found_count': search_data.get('found_count', 0),
                'results_file': search_data.get('results_file'),
                'export_files': search_data.get('export_files', [])
            }
            
            if existing_search is not None:
                # Update existing search instead of creating duplicate
                history['searches'][existing_search] = search_entry
                print(f"Updated existing search {search_id} instead of creating duplicate")
            else:
                # Add new search to beginning of list (most recent first)
                history['searches'].insert(0, search_entry)
                print(f"Added new search {search_id} to history")
            
            # Keep only last 50 searches to prevent bloat
            if len(history['searches']) > 50:
                history['searches'] = history['searches'][:50]
            
            self._save_history(username, history)
            return True
            
        except Exception as e:
            print(f"Error adding search to history: {e}")
            return False
    
    def get_history(self, username: str, limit: Optional[int] = None) -> List[Dict]:
        """Get user search history"""
        try:
            history = self._load_history(username)
            searches = history.get('searches', [])
            
            if limit:
                searches = searches[:limit]
            
            return searches
            
        except Exception as e:
            print(f"Error loading history: {e}")
            return []
    
    def get_search(self, username: str, search_id: str) -> Optional[Dict]:
        """Get specific search from history"""
        try:
            history = self._load_history(username)
            searches = history.get('searches', [])
            
            for search in searches:
                if search.get('search_id') == search_id:
                    return search
            
            return None
            
        except Exception as e:
            print(f"Error getting search: {e}")
            return None
    
    def delete_search(self, username: str, search_id: str) -> bool:
        """Delete a specific search from history"""
        try:
            history = self._load_history(username)
            searches = history.get('searches', [])
            
            # Find and remove the search
            original_length = len(searches)
            searches = [s for s in searches if s.get('search_id') != search_id]
            
            if len(searches) < original_length:
                history['searches'] = searches
                self._save_history(username, history)
                
                # Also try to delete associated files
                self._cleanup_search_files(search_id)
                return True
            
            return False
            
        except Exception as e:
            print(f"Error deleting search: {e}")
            return False
    
    def clear_history(self, username: str) -> bool:
        """Clear all search history for user"""
        try:
            history = self._load_history(username)
            
            # Get all search IDs for cleanup
            search_ids = [s.get('search_id') for s in history.get('searches', []) if s.get('search_id')]
            
            # Clear searches
            history['searches'] = []
            self._save_history(username, history)
            
            # Cleanup associated files
            for search_id in search_ids:
                if search_id:
                    self._cleanup_search_files(search_id)
            
            return True
            
        except Exception as e:
            print(f"Error clearing history: {e}")
            return False
    
    def _cleanup_search_files(self, search_id: str):
        """Clean up files associated with a search"""
        try:
            # Clean up results files
            results_dir = 'results'
            if os.path.exists(results_dir):
                for filename in os.listdir(results_dir):
                    if search_id in filename:
                        file_path = os.path.join(results_dir, filename)
                        try:
                            os.remove(file_path)
                        except OSError:
                            pass
            
            # Clean up upload files if they contain search_id
            uploads_dir = 'uploads'
            if os.path.exists(uploads_dir):
                for filename in os.listdir(uploads_dir):
                    if search_id in filename:
                        file_path = os.path.join(uploads_dir, filename)
                        try:
                            os.remove(file_path)
                        except OSError:
                            pass
                            
        except Exception:
            pass  # Fail silently for cleanup
    
    def get_history_stats(self, username: str) -> Dict:
        """Get history statistics for user"""
        try:
            history = self._load_history(username)
            searches = history.get('searches', [])
            
            if not searches:
                return {
                    'total_searches': 0,
                    'total_usernames_searched': 0,
                    'total_results_found': 0,
                    'first_search': None,
                    'last_search': None
                }
            
            total_usernames = sum(len(s.get('usernames', [])) for s in searches)
            total_found = sum(s.get('found_count', 0) for s in searches)
            
            # Get date range
            timestamps = [s.get('timestamp') for s in searches if s.get('timestamp')]
            first_search = min(timestamps) if timestamps else None
            last_search = max(timestamps) if timestamps else None
            
            return {
                'total_searches': len(searches),
                'total_usernames_searched': total_usernames,
                'total_results_found': total_found,
                'first_search': first_search,
                'last_search': last_search
            }
            
        except Exception as e:
            print(f"Error getting history stats: {e}")
            return {
                'total_searches': 0,
                'total_usernames_searched': 0,
                'total_results_found': 0,
                'first_search': None,
                'last_search': None
            }
    
    def update_search_status(self, username: str, search_id: str, status: str, 
                           results_count: int = 0, found_count: int = 0, 
                           results_file: Optional[str] = None, export_files: Optional[List[str]] = None) -> bool:
        """Update search status and results info"""
        try:
            history = self._load_history(username)
            searches = history.get('searches', [])
            
            for search in searches:
                if search.get('search_id') == search_id:
                    search['status'] = status
                    search['results_count'] = results_count
                    search['found_count'] = found_count
                    if results_file:
                        search['results_file'] = results_file
                    if export_files is not None:
                        search['export_files'] = export_files
                    break
            
            history['searches'] = searches
            self._save_history(username, history)
            return True
            
        except Exception as e:
            print(f"Error updating search status: {e}")
            return False
    
    def get_search_results(self, username: str, search_id: str) -> Optional[Dict]:
        """Get search results from results file"""
        try:
            search = self.get_search(username, search_id)
            if not search or not search.get('results_file'):
                return None
            
            results_file = search['results_file']
            if not os.path.exists(results_file):
                return None
            
            with open(results_file, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            print(f"Error loading search results: {e}")
            return None
    
    def export_history(self, username: str) -> Optional[str]:
        """Export user history to JSON file"""
        try:
            history = self._load_history(username)
            
            # Create export filename
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            export_filename = f"history_export_{username}_{timestamp}.json"
            export_path = os.path.join('uploads', export_filename)
            
            # Ensure uploads directory exists
            os.makedirs('uploads', exist_ok=True)
            
            # Save export file
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
            
            return export_path
            
        except Exception as e:
            print(f"Error exporting history: {e}")
            return None