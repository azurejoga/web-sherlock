import os
import json
import base64
import bcrypt
import uuid
import logging
import threading
import zipfile
import re
import pyotp
import jwt
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend

# Basic config, sensitive data from .env
JWT_SECRET = os.getenv('JWT_SECRET', 'your_jwt_secret_here')
JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
JWT_ISSUER = os.getenv('JWT_ISSUER', 'secureapp')
AES_KEY_RAW = base64.b64decode(os.getenv('AES_KEY_BASE64', base64.b64encode(os.urandom(32)).decode()))
PBKDF2_SALT = os.getenv('PBKDF2_SALT', 'fixed_salt_for_demo').encode()
PBKDF2_ITERATIONS = 100_000

USERNAME_REGEX = re.compile(r'^[a-zA-Z0-9_-]{3,30}$')

MAX_ATTEMPTS = 5
BLOCK_WINDOW = timedelta(minutes=5)

FAILED_LOGINS = {}
REVOKED_JTI = set()
LOCK = threading.Lock()


def derive_key(key_raw: bytes, salt: bytes = PBKDF2_SALT) -> bytes:
    """Derive AES key with PBKDF2"""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
        backend=default_backend()
    )
    return kdf.derive(key_raw)


class SecureStorage:
    """AES-GCM encryption with derived key"""
    def __init__(self, key_raw: bytes):
        self.key = derive_key(key_raw)

    def encrypt(self, data: bytes) -> bytes:
        aesgcm = AESGCM(self.key)
        nonce = os.urandom(12)
        ct = aesgcm.encrypt(nonce, data, None)
        return base64.b64encode(nonce + ct)

    def decrypt(self, enc_data: bytes) -> bytes:
        raw = base64.b64decode(enc_data)
        nonce = raw[:12]
        ct = raw[12:]
        aesgcm = AESGCM(self.key)
        return aesgcm.decrypt(nonce, ct, None)


class AuthManager:
    def __init__(self):
        self.storage = SecureStorage(AES_KEY_RAW)
        self.users_file = 'users.aes'
        self.history_dir = 'history'
        os.makedirs(self.history_dir, exist_ok=True)
        if not os.path.exists(self.users_file):
            self.save_users({})

    def _load_users(self) -> Dict[str, Any]:
        try:
            with open(self.users_file, 'rb') as f:
                decrypted = self.storage.decrypt(f.read())
                return json.loads(decrypted)
        except Exception:
            logging.exception("Failed to load users")
            return {}

    def save_users(self, users: Dict[str, Any]) -> None:
        try:
            raw = json.dumps(users, indent=2).encode()
            encrypted = self.storage.encrypt(raw)
            with open(self.users_file, 'wb') as f:
                f.write(encrypted)
        except Exception:
            logging.exception("Failed to save users")

    def hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()

    def verify_password(self, password: str, hashed: str) -> bool:
        try:
            return bcrypt.checkpw(password.encode(), hashed.encode())
        except Exception:
            return False

    def _rate_limit_check(self, username: str) -> bool:
        now = datetime.utcnow()
        attempts = FAILED_LOGINS.get(username, [])
        attempts = [ts for ts in attempts if now - ts < BLOCK_WINDOW]
        FAILED_LOGINS[username] = attempts
        return len(attempts) >= MAX_ATTEMPTS

    def _record_failed_login(self, username: str) -> None:
        now = datetime.utcnow()
        attempts = FAILED_LOGINS.get(username, [])
        attempts.append(now)
        FAILED_LOGINS[username] = attempts

    def generate_token(self, username: str) -> str:
        jti = str(uuid.uuid4())
        payload = {
            'username': username,
            'iss': JWT_ISSUER,
            'jti': jti,
            'exp': datetime.utcnow() + timedelta(hours=1)
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    def revoke_token(self, token: str) -> None:
        try:
            decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM], options={"verify_exp": False})
            jti = decoded.get('jti')
            if jti:
                with LOCK:
                    REVOKED_JTI.add(jti)
        except Exception:
            logging.exception("Token revocation failed")

    def verify_token(self, token: str) -> Optional[str]:
        try:
            decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM], issuer=JWT_ISSUER)
            jti = decoded.get('jti')
            with LOCK:
                if jti and jti in REVOKED_JTI:
                    return None
            return decoded.get('username')
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, jwt.InvalidIssuerError):
            return None

    def register_user(self, username: str, email: str, password: str) -> Dict[str, Any]:
        if not USERNAME_REGEX.match(username):
            return {'success': False, 'error': 'invalid_username_format'}

        users = self._load_users()
        if username in users:
            return {'success': False, 'error': 'user_exists'}
        if any(u.get('email') == email for u in users.values()):
            return {'success': False, 'error': 'email_exists'}

        secret_2fa = pyotp.random_base32()
        users[username] = {
            'email': email,
            'password_hash': self.hash_password(password),
            '2fa_secret': secret_2fa,
            'created_at': datetime.utcnow().isoformat(),
            'last_login': None
        }
        self.save_users(users)
        return {'success': True, 'username': username, '2fa_secret': secret_2fa}

    def verify_2fa(self, username: str, otp_code: str) -> bool:
        users = self._load_users()
        user = users.get(username)
        if not user:
            return False
        secret = user.get('2fa_secret')
        if not secret:
            return False
        totp = pyotp.TOTP(secret)
        return totp.verify(otp_code)

    def authenticate_user(self, username: str, password: str, otp_code: str) -> Dict[str, Any]:
        if self._rate_limit_check(username):
            return {'success': False, 'error': 'too_many_attempts'}

        users = self._load_users()
        user = users.get(username)
        if not user or not self.verify_password(password, user['password_hash']):
            self._record_failed_login(username)
            return {'success': False, 'error': 'invalid_credentials'}

        if not self.verify_2fa(username, otp_code):
            return {'success': False, 'error': 'invalid_otp'}

        user['last_login'] = datetime.utcnow().isoformat()
        self.save_users(users)

        with LOCK:
            FAILED_LOGINS.pop(username, None)

        token = self.generate_token(username)
        return {'success': True, 'token': token, 'email': user['email']}

    def get_user_info(self, username: str) -> Optional[Dict[str, Any]]:
        users = self._load_users()
        if username in users:
            data = users[username].copy()
            data.pop('password_hash', None)
            data.pop('2fa_secret', None)
            return data
        return None

    def save_user_search_history(self, username: str, search_data: Dict[str, Any]) -> None:
        path = os.path.join(self.history_dir, f'history_{username}.aes')
        try:
            if os.path.exists(path):
                with open(path, 'rb') as f:
                    dec = self.storage.decrypt(f.read())
                    history = json.loads(dec)
            else:
                history = []

            entry = {
                'search_id': search_data.get('search_id'),
                'usernames': search_data.get('usernames', []),
                'search_timestamp': search_data.get('search_timestamp', datetime.utcnow().isoformat()),
                'total_sites_checked': search_data.get('total_sites_checked', 0),
                'profiles_found': len(search_data.get('found_profiles', [])),
                'profiles_not_found': len(search_data.get('not_found_profiles', [])),
                'found_profiles': search_data.get('found_profiles', []),
                'not_found_profiles': search_data.get('not_found_profiles', [])
            }

            history.append(entry)
            history = history[-50:]

            raw = json.dumps(history, indent=2).encode()
            enc = self.storage.encrypt(raw)
            with open(path, 'wb') as f:
                f.write(enc)
        except Exception:
            logging.exception("Failed to save search history")

    def get_user_search_history(self, username: str) -> List[Dict[str, Any]]:
        path = os.path.join(self.history_dir, f'history_{username}.aes')
        try:
            if os.path.exists(path):
                with open(path, 'rb') as f:
                    dec = self.storage.decrypt(f.read())
                    history = json.loads(dec)
                    return sorted(history, key=lambda x: x.get('search_timestamp', ''), reverse=True)
            return []
        except Exception:
            logging.exception("Failed to load search history")
            return []

    def clear_user_search_history(self, username: str) -> bool:
        path = os.path.join(self.history_dir, f'history_{username}.aes')
        try:
            if os.path.exists(path):
                os.remove(path)
                return True
            return False
        except Exception:
            logging.exception("Failed to clear search history")
            return False


class SearchManager:
    def __init__(self):
        self.progress_tracker = {}
        self.progress_lock = threading.Lock()

    def run_search(self, usernames: List[str], options: Dict[str, Any], search_id: str, translations: Dict[str, str]) -> Dict:
        if not isinstance(usernames, list) or not all(isinstance(u, str) and USERNAME_REGEX.match(u) for u in usernames):
            raise ValueError("Invalid usernames list")

        results = {
            'found_profiles': [],
            'not_found_profiles': [],
            'total_sites_checked': 0,
            'search_timestamp': datetime.utcnow().isoformat()
        }

        total_usernames = len(usernames)
        estimated_sites_per_user = 50
        current_operation = 0

        with self.progress_lock:
            self.progress_tracker[search_id] = {
                'progress': 5,
                'message': translations.get('search_starting', 'Starting search...'),
                'status': 'running',
                'current_site': '',
                'sites_checked': 0,
                'total_sites': 0
            }

        for i, username in enumerate(usernames):
            base_progress = int((i / total_usernames) * 85) + 5

            with self.progress_lock:
                self.progress_tracker[search_id]['progress'] = base_progress
                self.progress_tracker[search_id]['message'] = f"{translations.get('searching_user', 'Searching user')} {username}..."
                self.progress_tracker[search_id]['current_site'] = ''
                self.progress_tracker[search_id]['sites_checked'] = current_operation

            user_results = self._search_username(username, options)

            sites_checked = 0
            for site_name, site_data in user_results.items():
                sites_checked += 1
                user_progress = base_progress + int((sites_checked / len(user_results)) * (85 / total_usernames))
                with self.progress_lock:
                    self.progress_tracker[search_id]['progress'] = min(user_progress, 90)
                    self.progress_tracker[search_id]['current_site'] = site_name
                    self.progress_tracker[search_id]['sites_checked'] = current_operation + sites_checked

                profile_data = {
                    'username': username,
                    'site': site_name,
                    'data': site_data
                }

                if site_data:
                    results['found_profiles'].append(profile_data)
                else:
                    results['not_found_profiles'].append(profile_data)

            current_operation += sites_checked

        with self.progress_lock:
            self.progress_tracker[search_id]['progress'] = 95
            self.progress_tracker[search_id]['message'] = translations.get('processing_results', 'Processing results...')
            self.progress_tracker[search_id]['current_site'] = ''

        results['total_sites_checked'] = len(results['found_profiles']) + len(results['not_found_profiles'])
        results['search_timestamp'] = datetime.utcnow().isoformat()

        with self.progress_lock:
            self.progress_tracker[search_id]['total_sites'] = results['total_sites_checked']
            self.progress_tracker[search_id]['status'] = 'completed'

        return results

    def _search_username(self, username: str, options: Dict[str, Any]) -> Dict[str, Any]:
        # Dummy implementation - replace with real site queries
        return {}

