import os
import time
import hashlib
import secrets
from typing import Optional, Dict, Any, Union
from datetime import datetime, timedelta
import json
import base64
import hmac

try:
    from passlib.context import CryptContext
except ImportError:
    CryptContext = None

from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .config import get_config


class PasswordManager:
    """Password hashing and verification utilities."""
    
    def __init__(self, schemes: list = None):
        if CryptContext is None:
            raise ImportError("passlib is required for password hashing. Install with: pip install passlib[bcrypt]")
        self.schemes = schemes or ["bcrypt"]
        self.pwd_context = CryptContext(schemes=self.schemes, deprecated="auto")
    
    def hash_password(self, password: str) -> str:
        """Hash a password."""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def generate_random_password(self, length: int = 12) -> str:
        """Generate a random password."""
        return secrets.token_urlsafe(length)


class JWTManager:
    """JWT token management utilities."""
    
    def __init__(self, secret_key: str = None, algorithm: str = "HS256"):
        self.config = get_config()
        self.secret_key = secret_key or self.config.secret_key
        self.algorithm = algorithm or self.config.jwt_algorithm
        self.access_token_expire = self.config.jwt_expiry
        self.refresh_token_expire = self.config.jwt_refresh_expiry
        
        if self.secret_key == "dev-secret-key-change-in-production":
            raise ValueError("Change the SECRET_KEY in production!")
    
    def _base64url_encode(self, data: bytes) -> str:
        """Base64 URL-safe encode."""
        return base64.urlsafe_b64encode(data).decode().rstrip('=')
    
    def _base64url_decode(self, data: str) -> bytes:
        """Base64 URL-safe decode."""
        # Add padding if needed
        padding = 4 - len(data) % 4
        if padding != 4:
            data += '=' * padding
        return base64.urlsafe_b64decode(data)
    
    def _create_signature(self, header: str, payload: str) -> str:
        """Create JWT signature."""
        message = f"{header}.{payload}"
        signature = hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).digest()
        return self._base64url_encode(signature)
    
    def create_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None,
        token_type: str = "access"
    ) -> str:
        """Create a JWT token."""
        # Create header
        header = {
            "alg": self.algorithm,
            "typ": "JWT"
        }
        
        # Create payload
        to_encode = data.copy()
        
        # Set expiration
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire_minutes = self.access_token_expire if token_type == "access" else self.refresh_token_expire
            expire = datetime.utcnow() + timedelta(seconds=expire_minutes)
        
        to_encode.update({
            "exp": int(expire.timestamp()),
            "iat": int(datetime.utcnow().timestamp()),
            "type": token_type
        })
        
        # Encode header and payload
        header_encoded = self._base64url_encode(json.dumps(header).encode())
        payload_encoded = self._base64url_encode(json.dumps(to_encode).encode())
        
        # Create signature
        signature = self._create_signature(header_encoded, payload_encoded)
        
        # Return complete token
        return f"{header_encoded}.{payload_encoded}.{signature}"
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token."""
        try:
            parts = token.split('.')
            if len(parts) != 3:
                return None
            
            header_encoded, payload_encoded, signature = parts
            
            # Verify signature
            expected_signature = self._create_signature(header_encoded, payload_encoded)
            if not hmac.compare_digest(signature, expected_signature):
                return None
            
            # Decode payload
            payload_data = json.loads(self._base64url_decode(payload_encoded))
            
            # Check expiration
            if 'exp' in payload_data and payload_data['exp'] < time.time():
                return None
            
            return payload_data
            
        except Exception:
            return None
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create an access token."""
        return self.create_token(data, expires_delta, "access")
    
    def create_refresh_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a refresh token."""
        return self.create_token(data, expires_delta, "refresh")
    
    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """Create new access token from refresh token."""
        payload = self.verify_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            return None
        
        # Remove token-specific fields
        user_data = {k: v for k, v in payload.items() if k not in ['exp', 'iat', 'type']}
        return self.create_access_token(user_data)


class APIKeyManager:
    """API Key management utilities."""
    
    def __init__(self):
        self.config = get_config()
    
    def generate_api_key(self, length: int = 32) -> str:
        """Generate a new API key."""
        return secrets.token_urlsafe(length)
    
    def hash_api_key(self, api_key: str) -> str:
        """Hash an API key for storage."""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def verify_api_key(self, api_key: str, hashed_key: str) -> bool:
        """Verify an API key against its hash."""
        return hmac.compare_digest(self.hash_api_key(api_key), hashed_key)


class AuthDependencies:
    """FastAPI dependency classes for authentication."""
    
    def __init__(self, jwt_manager: JWTManager = None):
        self.jwt_manager = jwt_manager or JWTManager()
        self.bearer_scheme = HTTPBearer()
    
    async def get_current_user(
        self,
        credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
    ) -> Dict[str, Any]:
        """Dependency to get current authenticated user."""
        token = credentials.credentials
        payload = self.jwt_manager.verify_token(token)
        
        if not payload:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return payload
    
    async def get_current_active_user(
        self,
        current_user: Dict[str, Any] = Depends(lambda: AuthDependencies().get_current_user)
    ) -> Dict[str, Any]:
        """Dependency to get current active user."""
        if current_user.get("disabled"):
            raise HTTPException(status_code=400, detail="Inactive user")
        return current_user
    
    async def require_roles(self, required_roles: list):
        """Create a dependency that requires specific roles."""
        async def role_checker(
            current_user: Dict[str, Any] = Depends(self.get_current_user)
        ):
            user_roles = current_user.get("roles", [])
            if not any(role in user_roles for role in required_roles):
                raise HTTPException(
                    status_code=403,
                    detail="Insufficient permissions"
                )
            return current_user
        return role_checker
    
    async def require_permissions(self, required_permissions: list):
        """Create a dependency that requires specific permissions."""
        async def permission_checker(
            current_user: Dict[str, Any] = Depends(self.get_current_user)
        ):
            user_permissions = current_user.get("permissions", [])
            if not all(perm in user_permissions for perm in required_permissions):
                raise HTTPException(
                    status_code=403,
                    detail="Insufficient permissions"
                )
            return current_user
        return permission_checker


# Global instances (lazy initialization to handle import errors gracefully)
password_manager = None
jwt_manager = None
api_key_manager = APIKeyManager()
auth_deps = None

def _get_password_manager():
    global password_manager
    if password_manager is None:
        try:
            password_manager = PasswordManager()
        except ImportError:
            pass
    return password_manager

def _get_jwt_manager():
    global jwt_manager
    if jwt_manager is None:
        jwt_manager = JWTManager()
    return jwt_manager

def _get_auth_deps():
    global auth_deps
    if auth_deps is None:
        auth_deps = AuthDependencies()
    return auth_deps


def hash_password(password: str) -> str:
    """Hash a password using the global password manager."""
    manager = _get_password_manager()
    if manager is None:
        raise ImportError("passlib is required for password hashing. Install with: pip install passlib[bcrypt]")
    return manager.hash_password(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password using the global password manager."""
    manager = _get_password_manager()
    if manager is None:
        raise ImportError("passlib is required for password hashing. Install with: pip install passlib[bcrypt]")
    return manager.verify_password(plain_password, hashed_password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create an access token using the global JWT manager."""
    return _get_jwt_manager().create_access_token(data, expires_delta)


def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a refresh token using the global JWT manager."""
    return _get_jwt_manager().create_refresh_token(data, expires_delta)


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify a token using the global JWT manager."""
    return _get_jwt_manager().verify_token(token)


def get_current_user():
    """Get the current user dependency."""
    return _get_auth_deps().get_current_user


def get_current_active_user():
    """Get the current active user dependency."""
    return _get_auth_deps().get_current_active_user


def require_roles(roles: list):
    """Create a dependency that requires specific roles."""
    return _get_auth_deps().require_roles(roles)


def require_permissions(permissions: list):
    """Create a dependency that requires specific permissions."""
    return _get_auth_deps().require_permissions(permissions)


# Utility functions
def generate_api_key(length: int = 32) -> str:
    """Generate a new API key."""
    return api_key_manager.generate_api_key(length)


def generate_password(length: int = 12) -> str:
    """Generate a random password."""
    manager = _get_password_manager()
    if manager is None:
        raise ImportError("passlib is required for password generation. Install with: pip install passlib[bcrypt]")
    return manager.generate_random_password(length)


class TokenResponse:
    """Standard token response format."""
    
    def __init__(self, access_token: str, refresh_token: str = None, token_type: str = "bearer"):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.token_type = token_type
    
    def dict(self):
        result = {
            "access_token": self.access_token,
            "token_type": self.token_type
        }
        if self.refresh_token:
            result["refresh_token"] = self.refresh_token
        return result


def create_token_response(user_data: Dict[str, Any]) -> TokenResponse:
    """Create a standard token response with access and refresh tokens."""
    access_token = create_access_token(user_data)
    refresh_token = create_refresh_token(user_data)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)