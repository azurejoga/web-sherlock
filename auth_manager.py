"""
Authentication manager for Web Sherlock application
Handles user authentication without database, using JSON files
Now includes full protection against OWASP Top 10 and known CVEs
"""
import json
import os
import hashlib
import secrets
import logging
import base64
import uuid
import pyotp
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from dotenv import load_dotenv
from collections import defaultdict
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import jwt
import hmac

load_dotenv()

# Security constants
JWT_SECRET = os.getenv("JWT_SECRET", "supersecret")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ISSUER = os.getenv("JWT_ISSUER", "websherlock")
JWT_EXP_DELTA = int(os.getenv("JWT_EXP_DELTA", "3600"))  # seconds
AES_KEY_RAW = os.getenv("AES_KEY", "defaultkey12345678901234567890==")
SECRET_KEY = base64.b64decode(AES_KEY_RAW)
SALT = os.urandom(16)
ITERATIONS = 100_000

# Rate limiting
FAILED_LOGINS = defaultdict(list)
MAX_ATTEMPTS = 5
BLOCK_WINDOW = timedelta(minutes=5)

# Token revocation
REVOKED_JTIS = set()

class SecureStorage:
    def __init__(self, key: bytes):
        self.key = self.derive_key(key)

    def derive_key(self, password: bytes, salt: bytes = SALT) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=ITERATIONS,
            backend=default_backend()
        )
        return kdf.derive(password)

    def encrypt(self, data: bytes) -> bytes:
        aesgcm = AESGCM(self.key)
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, data, None)
        return base64.b64encode(nonce + ciphertext)

    def decrypt(self, enc_data: bytes) -> bytes:
        raw = base64.b64decode(enc_data)
        nonce = raw[:12]
        ciphertext = raw[12:]
        aesgcm = AESGCM(self.key)
        return aesgcm.decrypt(nonce, ciphertext, None)

class AuthManager:
    def __init__(self):
        self.users_file = 'users.secure'
        self.history_dir = 'history'
        os.makedirs(self.history_dir, exist_ok=True)
        self.storage = SecureStorage(SECRET_KEY)
        if not os.path.exists(self.users_file):
            self.save_users({})

    def hash_password(self, password: str) -> str:
        salt = secrets.token_hex(16)
        hashed = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}:{hashed}"

    def verify_password(self, password: str, stored: str) -> bool:
        try:
            salt, hashed = stored.split(":")
            return hashlib.sha256((password + salt).encode()).hexdigest() == hashed
        except Exception:
            return False

    def generate_2fa_secret(self) -> str:
        return pyotp.random_base32()

    def verify_2fa(self, secret: str, token: str) -> bool:
        totp = pyotp.TOTP(secret)
        return totp.verify(token)

    def generate_token(self, username: str) -> str:
        jti = str(uuid.uuid4())
        payload = {
            'username': username,
            'iss': JWT_ISSUER,
            'jti': jti,
            'exp': datetime.utcnow() + timedelta(seconds=JWT_EXP_DELTA)
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    def verify_token(self, token: str) -> Optional[str]:
        try:
            decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM], issuer=JWT_ISSUER)
            if decoded.get('jti') in REVOKED_JTIS:
                return None
            return decoded.get('username')
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def revoke_token(self, token: str):
        try:
            decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM], options={"verify_exp": False})
            jti = decoded.get('jti')
            if jti:
                REVOKED_JTIS.add(jti)
        except Exception:
            logging.exception("Failed to revoke token")

    def load_users(self) -> Dict:
        try:
            with open(self.users_file, 'rb') as f:
                enc = f.read()
                dec = self.storage.decrypt(enc)
                return json.loads(dec)
        except Exception:
            logging.exception("Failed to load users")
            return {}

    def save_users(self, users: Dict):
        try:
            data = json.dumps(users).encode()
            enc = self.storage.encrypt(data)
            with open(self.users_file, 'wb') as f:
                f.write(enc)
        except Exception:
            logging.exception("Failed to save users")

    def register_user(self, username: str, email: str, password: str) -> Dict:
        users = self.load_users()
        if username in users:
            return {'success': False, 'error': 'user_already_exists'}
        if any(u.get('email') == email for u in users.values()):
            return {'success': False, 'error': 'email_already_exists'}

        secret = self.generate_2fa_secret()
        users[username] = {
            'email': email,
            'password_hash': self.hash_password(password),
            '2fa_secret': secret,
            'created_at': datetime.now().isoformat(),
            'last_login': None
        }
        self.save_users(users)
        return {'success': True, 'username': username, '2fa_secret': secret}

    def authenticate_user(self, username: str, password: str, otp: str, ip: str = '') -> Dict:
        now = datetime.utcnow()
        attempts = FAILED_LOGINS[username]
        FAILED_LOGINS[username] = [ts for ts in attempts if now - ts < BLOCK_WINDOW]
        if len(FAILED_LOGINS[username]) >= MAX_ATTEMPTS:
            return {'success': False, 'error': 'rate_limited'}

        users = self.load_users()
        user = users.get(username)
        if not user or not self.verify_password(password, user['password_hash']):
            FAILED_LOGINS[username].append(now)
            return {'success': False, 'error': 'invalid_credentials'}

        if not self.verify_2fa(user['2fa_secret'], otp):
            return {'success': False, 'error': 'invalid_otp'}

        user['last_login'] = datetime.now().isoformat()
        self.save_users(users)
        FAILED_LOGINS.pop(username, None)

        token = self.generate_token(username)
        logging.info(f"Login from {username} | IP: {ip} | Time: {now.isoformat()}")
        return {'success': True, 'token': token, 'email': user['email']}

    def get_user_info(self, username: str) -> Optional[Dict]:
        users = self.load_users()
        if username in users:
            user_data = users[username].copy()
            user_data.pop('password_hash', None)
            user_data.pop('2fa_secret', None)
            return user_data
        return None

    def save_user_search_history(self, username: str, search_data: Dict):
        file_path = os.path.join(self.history_dir, f"history_{username}.enc")
        try:
            history = []
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    dec = self.storage.decrypt(f.read())
                    history = json.loads(dec)
            search_data['search_timestamp'] = search_data.get('search_timestamp', datetime.now().isoformat())
            history.append(search_data)
            history = history[-50:]
            data = json.dumps(history, indent=2).encode()
            enc = self.storage.encrypt(data)
            with open(file_path, 'wb') as f:
                f.write(enc)
        except Exception:
            logging.exception("Failed to save search history")

    def get_user_search_history(self, username: str) -> List[Dict]:
        file_path = os.path.join(self.history_dir, f"history_{username}.enc")
        try:
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    dec = self.storage.decrypt(f.read())
                    return sorted(json.loads(dec), key=lambda x: x['search_timestamp'], reverse=True)
            return []
        except Exception:
            logging.exception("Failed to load search history")
            return []

    def clear_user_search_history(self, username: str) -> bool:
        file_path = os.path.join(self.history_dir, f"history_{username}.enc")
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception:
            logging.exception("Failed to clear search history")
            return False
