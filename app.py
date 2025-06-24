import os
import json
import bcrypt
import base64
import logging
import jwt
import uuid
import pyotp
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from dotenv import load_dotenv
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from collections import defaultdict

load_dotenv()

# Security settings
SECRET_KEY = base64.b64decode(os.getenv('AES_KEY'))
JWT_SECRET = os.getenv('JWT_SECRET')
JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
JWT_ISSUER = os.getenv('JWT_ISSUER', 'secureapp')
SALT = os.urandom(16)
ITERATIONS = 100000

# Token blacklist for revocation
REVOKED_JTI = set()

# Rate limiting
FAILED_LOGINS = defaultdict(list)
MAX_ATTEMPTS = 5
BLOCK_WINDOW = timedelta(minutes=5)


def derive_key(password: bytes, salt: bytes = SALT) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=ITERATIONS,
        backend=default_backend()
    )
    return kdf.derive(password)


class SecureStorage:
    def _init_(self, key: bytes):
        self.key = derive_key(key)

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
    def _init_(self):
        self.storage = SecureStorage(SECRET_KEY)
        self.users_file = 'users.aes'
        self.history_dir = 'history'
        os.makedirs(self.history_dir, exist_ok=True)
        if not os.path.exists(self.users_file):
            self.save_users({})

    def hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()

    def verify_password(self, password: str, hashed: str) -> bool:
        try:
            return bcrypt.checkpw(password.encode(), hashed.encode())
        except ValueError:
            return False

    def load_users(self) -> Dict:
        try:
            with open(self.users_file, 'rb') as f:
                enc = f.read()
                decrypted = self.storage.decrypt(enc)
                return json.loads(decrypted)
        except Exception:
            logging.exception("Failed to load users")
            return {}

    def save_users(self, users: Dict):
        try:
            raw = json.dumps(users, indent=2).encode()
            enc = self.storage.encrypt(raw)
            with open(self.users_file, 'wb') as f:
                f.write(enc)
        except Exception:
            logging.exception("Failed to save users")

    def generate_token(self, username: str) -> str:
        jti = str(uuid.uuid4())
        payload = {
            'username': username,
            'iss': JWT_ISSUER,
            'jti': jti,
            'exp': datetime.utcnow() + timedelta(hours=1)
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    def revoke_token(self, token: str):
        try:
            decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM], options={"verify_exp": False})
            jti = decoded.get('jti')
            if jti:
                REVOKED_JTI.add(jti)
        except Exception:
            logging.exception("Token revocation failed")

    def verify_token(self, token: str) -> Optional[str]:
        try:
            decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM], issuer=JWT_ISSUER)
            jti = decoded.get('jti')
            if jti and jti in REVOKED_JTI:
                return None
            return decoded.get('username')
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, jwt.InvalidIssuerError):
            return None

    def register_user(self, username: str, email: str, password: str) -> Dict:
        users = self.load_users()
        if username in users:
            return {'success': False, 'error': 'user_exists'}
        if any(u.get('email') == email for u in users.values()):
            return {'success': False, 'error': 'email_exists'}
        secret_2fa = pyotp.random_base32()
        users[username] = {
            'email': email,
            'password_hash': self.hash_password(password),
            '2fa_secret': secret_2fa,
            'created_at': datetime.now().isoformat(),
            'last_login': None
        }
        self.save_users(users)
        return {'success': True, 'username': username, '2fa_secret': secret_2fa}

    def verify_2fa(self, username: str, token: str) -> bool:
        users = self.load_users()
        user = users.get(username)
        if not user:
            return False
        secret = user.get('2fa_secret')
        if not secret:
            return False
        totp = pyotp.TOTP(secret)
        return totp.verify(token)

    def authenticate_user(self, username: str, password: str, otp_code: str) -> Dict:
        now = datetime.utcnow()
        attempts = FAILED_LOGINS[username]
        FAILED_LOGINS[username] = [ts for ts in attempts if now - ts < BLOCK_WINDOW]
        if len(FAILED_LOGINS[username]) >= MAX_ATTEMPTS:
            return {'success': False, 'error': 'too_many_attempts'}

        users = self.load_users()
        user = users.get(username)
        if not user or not self.verify_password(password, user['password_hash']):
            FAILED_LOGINS[username].append(now)
            return {'success': False, 'error': 'invalid_credentials'}

        if not self.verify_2fa(username, otp_code):
            return {'success': False, 'error': 'invalid_otp'}

        user['last_login'] = datetime.now().isoformat()
        self.save_users(users)
        token = self.generate_token(username)
        FAILED_LOGINS.pop(username, None)
        return {'success': True, 'token': token, 'email': user['email']}

    def get_user_info(self, username: str) -> Optional[Dict]:
        users = self.load_users()
        if username in users:
            data = users[username].copy()
            data.pop('password_hash', None)
            data.pop('2fa_secret', None)
            return data
        return None

    def save_user_search_history(self, username: str, search_data: Dict):
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
                'search_timestamp': search_data.get('search_timestamp', datetime.now().isoformat()),
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

    def get_user_search_history(self, username: str) -> List[Dict]:
        path = os.path.join(self.history_dir, f'history_{username}.aes')
        try:
            if os.path.exists(path):
                with open(path, 'rb') as f:
                    dec = self.storage.decrypt(f.read())
                    history = json.loads(dec)
                    return sorted(history, key=lambda x: x['search_timestamp'], reverse=True)
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