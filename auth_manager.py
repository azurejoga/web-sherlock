"""
Authentication manager for Web Sherlock application
Handles user authentication without database, using JSON files
"""
import json
import os
import hashlib
import secrets
from datetime import datetime
from typing import Dict, Optional, List
import logging

class AuthManager:
    def __init__(self):
        self.users_file = 'users.json'
        self.ensure_users_file()
    
    def ensure_users_file(self):
        """Ensure users.json file exists"""
        if not os.path.exists(self.users_file):
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump({}, f, indent=2)
    
    def hash_password(self, password: str) -> str:
        """Hash password using SHA-256 with salt"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}:{password_hash}"
    
    def verify_password(self, password: str, hash_with_salt: str) -> bool:
        """Verify password against hash"""
        try:
            salt, stored_hash = hash_with_salt.split(':')
            password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
            return password_hash == stored_hash
        except ValueError:
            return False
    
    def load_users(self) -> Dict:
        """Load users from JSON file"""
        try:
            with open(self.users_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def save_users(self, users: Dict):
        """Save users to JSON file"""
        with open(self.users_file, 'w', encoding='utf-8') as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
    
    def register_user(self, username: str, email: str, password: str) -> Dict:
        """Register a new user"""
        users = self.load_users()
        
        # Check if user already exists
        if username in users:
            return {'success': False, 'error': 'user_already_exists'}
        
        # Check if email already exists
        for user_data in users.values():
            if user_data.get('email') == email:
                return {'success': False, 'error': 'email_already_exists'}
        
        # Create new user
        password_hash = self.hash_password(password)
        users[username] = {
            'email': email,
            'password_hash': password_hash,
            'created_at': datetime.now().isoformat(),
            'last_login': None
        }
        
        self.save_users(users)
        logging.info(f"New user registered: {username}")
        return {'success': True, 'username': username}
    
    def authenticate_user(self, username: str, password: str) -> Dict:
        """Authenticate user"""
        users = self.load_users()
        
        if username not in users:
            return {'success': False, 'error': 'invalid_credentials'}
        
        user_data = users[username]
        if not self.verify_password(password, user_data['password_hash']):
            return {'success': False, 'error': 'invalid_credentials'}
        
        # Update last login
        users[username]['last_login'] = datetime.now().isoformat()
        self.save_users(users)
        
        logging.info(f"User authenticated: {username}")
        return {'success': True, 'username': username, 'email': user_data['email']}
    
    def get_user_info(self, username: str) -> Optional[Dict]:
        """Get user information"""
        users = self.load_users()
        if username in users:
            user_data = users[username].copy()
            user_data.pop('password_hash', None)  # Remove password hash
            return user_data
        return None
    
    def save_user_search_history(self, username: str, search_data: Dict):
        """Save search to user's history"""
        history_file = f'history_{username}.json'
        
        try:
            # Load existing history
            if os.path.exists(history_file):
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            else:
                history = []
            
            # Add new search with complete data for viewing
            search_entry = {
                'search_id': search_data.get('search_id'),
                'usernames': search_data.get('usernames', []),
                'timestamp': search_data.get('search_timestamp', datetime.now().isoformat()),
                'search_timestamp': search_data.get('search_timestamp', datetime.now().isoformat()),
                'total_sites_checked': search_data.get('total_sites_checked', 0),
                'profiles_found': len(search_data.get('found_profiles', [])),
                'profiles_not_found': len(search_data.get('not_found_profiles', [])),
                # Store complete results for viewing
                'found_profiles': search_data.get('found_profiles', []),
                'not_found_profiles': search_data.get('not_found_profiles', [])
            }
            
            history.append(search_entry)
            
            # Keep only last 50 searches
            if len(history) > 50:
                history = history[-50:]
            
            # Save history
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
                
            logging.info(f"Search history saved for user: {username}")
            
        except Exception as e:
            logging.error(f"Error saving search history for {username}: {str(e)}")
    
    def get_user_search_history(self, username: str) -> List[Dict]:
        """Get user's search history"""
        history_file = f'history_{username}.json'
        
        try:
            if os.path.exists(history_file):
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                    # Return in reverse order (newest first)
                    return sorted(history, key=lambda x: x.get('timestamp', ''), reverse=True)
            return []
        except Exception as e:
            logging.error(f"Error loading search history for {username}: {str(e)}")
            return []
    
    def delete_search_history_item(self, username: str, search_id: str) -> bool:
        """Delete a specific search from user's history"""
        history_file = f'history_{username}.json'
        
        try:
            if os.path.exists(history_file):
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                
                # Filter out the search with the given ID
                updated_history = [search for search in history if search.get('search_id') != search_id]
                
                # Save updated history
                with open(history_file, 'w', encoding='utf-8') as f:
                    json.dump(updated_history, f, indent=2, ensure_ascii=False)
                
                logging.info(f"Search {search_id} deleted from history for user: {username}")
                return True
            return False
        except Exception as e:
            logging.error(f"Error deleting search history item for {username}: {str(e)}")
            return False
    
    def clear_user_search_history(self, username: str) -> bool:
        """Clear all search history for a user"""
        history_file = f'history_{username}.json'
        
        try:
            if os.path.exists(history_file):
                os.remove(history_file)
                logging.info(f"Search history cleared for user: {username}")
                return True
            return False
        except Exception as e:
            logging.error(f"Error clearing search history for {username}: {str(e)}")
            return False
    
    def get_search_by_id(self, username: str, search_id: str) -> Optional[Dict]:
        """Get a specific search from user's history"""
        history = self.get_user_search_history(username)
        for search in history:
            if search.get('search_id') == search_id:
                return search
        return None