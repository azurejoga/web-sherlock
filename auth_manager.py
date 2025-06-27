"""
Authentication Manager for Web Sherlock
Handles user registration, login, and session management using JSON storage
Implements security best practices including bcrypt, JWT, and rate limiting
"""

import json
import os
import time
import uuid
import base64
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any

import bcrypt
import jwt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes


class AuthManager:
    def __init__(self, users_file='users.json', secret_key=None):
        self.users_file = users_file
        self.secret_key = secret_key or os.environ.get('SESSION_SECRET', 'default-secret-key')
        self.jwt_issuer = 'web-sherlock'
        self.jwt_algorithm = 'HS256'
        self.login_attempts = {}  # In-memory rate limiting
        self.max_attempts = 5
        self.lockout_duration = 300  # 5 minutes
        
        # Initialize users file if it doesn't exist
        self._init_users_file()
    
    def _init_users_file(self):
        """Initialize users.json file if it doesn't exist"""
        if not os.path.exists(self.users_file):
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'users': {},
                    'revoked_tokens': [],
                    'created_at': datetime.utcnow().isoformat()
                }, f, indent=2)
    
    def _load_users(self) -> Dict:
        """Load users data from JSON file"""
        try:
            with open(self.users_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self._init_users_file()
            return self._load_users()
    
    def _save_users(self, data: Dict):
        """Save users data to JSON file"""
        with open(self.users_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _rate_limit_check(self, username: str) -> bool:
        """Check if user is rate limited"""
        current_time = time.time()
        if username in self.login_attempts:
            attempts, last_attempt = self.login_attempts[username]
            if current_time - last_attempt < self.lockout_duration and attempts >= self.max_attempts:
                return True
            elif current_time - last_attempt >= self.lockout_duration:
                # Reset attempts after lockout period
                del self.login_attempts[username]
        return False
    
    def _record_login_attempt(self, username: str, success: bool):
        """Record login attempt for rate limiting"""
        current_time = time.time()
        if success:
            # Clear attempts on successful login
            if username in self.login_attempts:
                del self.login_attempts[username]
        else:
            if username in self.login_attempts:
                attempts, _ = self.login_attempts[username]
                self.login_attempts[username] = (attempts + 1, current_time)
            else:
                self.login_attempts[username] = (1, current_time)
    
    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def _verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception:
            return False
    
    def _generate_jwt(self, username: str) -> str:
        """Generate JWT token for user with enhanced security"""
        jti = str(uuid.uuid4())
        payload = {
            'username': username,
            'iss': self.jwt_issuer,
            'jti': jti,
            'exp': datetime.utcnow() + timedelta(hours=1),  # Reduced expiration time
            'iat': datetime.utcnow(),
            'nbf': datetime.utcnow()  # Not before timestamp
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.jwt_algorithm)
    
    def _verify_jwt(self, token: str) -> Optional[Dict]:
        """Verify JWT token with enhanced security checks"""
        try:
            # Check if token is revoked
            data = self._load_users()
            if token in data.get('revoked_tokens', []):
                return None
            
            # Decode with strict validation - reject "none" algorithm
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.jwt_algorithm],  # Only allow HS256
                issuer=self.jwt_issuer,
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_nbf": True,
                    "verify_iat": True,
                    "verify_iss": True,
                    "require": ["exp", "iat", "iss", "jti", "username"]
                }
            )
            
            # Additional validation
            if not payload.get('username'):
                return None
                
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        except Exception:
            return None
    
    def register_user(self, username: str, email: str, password: str) -> Dict[str, Any]:
        """Register a new user"""
        # Validate input
        if not username or not email or not password:
            return {'success': False, 'error': 'missing_fields'}
        
        if len(username) < 3 or len(username) > 50:
            return {'success': False, 'error': 'invalid_username_length'}
        
        if len(password) < 6:
            return {'success': False, 'error': 'password_too_short'}
        
        # Check if user already exists
        data = self._load_users()
        users = data.get('users', {})
        
        if username in users:
            return {'success': False, 'error': 'username_exists'}
        
        # Check if email already exists
        for user_data in users.values():
            if user_data.get('email') == email:
                return {'success': False, 'error': 'email_exists'}
        
        # Create new user
        hashed_password = self._hash_password(password)
        users[username] = {
            'email': email,
            'password_hash': hashed_password,
            'created_at': datetime.utcnow().isoformat(),
            'last_login': None,
            'active': True
        }
        
        data['users'] = users
        self._save_users(data)
        
        # Generate token for immediate login
        token = self._generate_jwt(username)
        
        return {
            'success': True,
            'token': token,
            'user': {
                'username': username,
                'email': email,
                'created_at': users[username]['created_at']
            }
        }
    
    def login_user(self, username: str, password: str) -> Dict[str, Any]:
        """Login user and return JWT token"""
        # Check rate limiting
        if self._rate_limit_check(username):
            return {'success': False, 'error': 'too_many_attempts'}
        
        # Validate input
        if not username or not password:
            self._record_login_attempt(username, False)
            return {'success': False, 'error': 'missing_credentials'}
        
        # Load users
        data = self._load_users()
        users = data.get('users', {})
        
        if username not in users:
            self._record_login_attempt(username, False)
            return {'success': False, 'error': 'invalid_credentials'}
        
        user_data = users[username]
        
        # Check if account is active
        if not user_data.get('active', True):
            self._record_login_attempt(username, False)
            return {'success': False, 'error': 'account_disabled'}
        
        # Verify password
        if not self._verify_password(password, user_data['password_hash']):
            self._record_login_attempt(username, False)
            return {'success': False, 'error': 'invalid_credentials'}
        
        # Update last login
        users[username]['last_login'] = datetime.utcnow().isoformat()
        data['users'] = users
        self._save_users(data)
        
        # Record successful login
        self._record_login_attempt(username, True)
        
        # Generate token
        token = self._generate_jwt(username)
        
        return {
            'success': True,
            'token': token,
            'user': {
                'username': username,
                'email': user_data['email'],
                'last_login': users[username]['last_login']
            }
        }
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify token and return user data"""
        payload = self._verify_jwt(token)
        if not payload:
            return None
        
        username = payload.get('username')
        if not username:
            return None
        
        # Get user data
        data = self._load_users()
        users = data.get('users', {})
        
        if username not in users or not users[username].get('active', True):
            return None
        
        return {
            'username': username,
            'email': users[username]['email']
        }
    
    def logout_user(self, token: str) -> bool:
        """Logout user by revoking token"""
        try:
            data = self._load_users()
            revoked_tokens = data.get('revoked_tokens', [])
            
            if token not in revoked_tokens:
                revoked_tokens.append(token)
                data['revoked_tokens'] = revoked_tokens
                self._save_users(data)
            
            return True
        except Exception:
            return False
    
    def get_user_profile(self, username: str) -> Optional[Dict]:
        """Get user profile data"""
        data = self._load_users()
        users = data.get('users', {})
        
        if username not in users:
            return None
        
        user_data = users[username]
        return {
            'username': username,
            'email': user_data['email'],
            'created_at': user_data['created_at'],
            'last_login': user_data.get('last_login'),
            'active': user_data.get('active', True)
        }
    
    def change_password(self, username: str, old_password: str, new_password: str) -> Dict[str, Any]:
        """Change user password"""
        if len(new_password) < 6:
            return {'success': False, 'error': 'password_too_short'}
        
        data = self._load_users()
        users = data.get('users', {})
        
        if username not in users:
            return {'success': False, 'error': 'user_not_found'}
        
        user_data = users[username]
        
        # Verify old password
        if not self._verify_password(old_password, user_data['password_hash']):
            return {'success': False, 'error': 'invalid_old_password'}
        
        # Update password
        users[username]['password_hash'] = self._hash_password(new_password)
        data['users'] = users
        self._save_users(data)
        
        return {'success': True}
    
    def cleanup_revoked_tokens(self):
        """Clean up expired revoked tokens"""
        try:
            data = self._load_users()
            revoked_tokens = data.get('revoked_tokens', [])
            
            # Filter out expired tokens
            valid_tokens = []
            for token in revoked_tokens:
                try:
                    jwt.decode(token, self.secret_key, algorithms=[self.jwt_algorithm])
                    valid_tokens.append(token)
                except jwt.ExpiredSignatureError:
                    # Token expired, don't keep it
                    pass
                except jwt.InvalidTokenError:
                    # Invalid token, don't keep it
                    pass
            
            if len(valid_tokens) != len(revoked_tokens):
                data['revoked_tokens'] = valid_tokens
                self._save_users(data)
            
        except Exception:
            pass  # Fail silently for cleanup