"""
PyNext - A Next.js-inspired file-based routing framework built on FastAPI
"""

__version__ = "0.1.0"
__author__ = "Amanpreet Singh"
__email__ = "amanpreetsinghjhiwant7@gmail.com"

# Core framework
from .core import create_app, create_pynext_app, PyNextApp

# Configuration
from .config import PyNextConfig, get_config, load_config

# Authentication
from .auth import (
    PasswordManager,
    JWTManager,
    APIKeyManager,
    AuthDependencies,
    TokenResponse,
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
    get_current_user,
    get_current_active_user,
    require_roles,
    require_permissions,
    generate_api_key,
    generate_password,
    create_token_response,
    password_manager,
    jwt_manager,
    api_key_manager,
    auth_deps,
)

# Middleware
from .middleware import (
    PyNextMiddleware,
    RequestLoggingMiddleware,
    RateLimitMiddleware,
    AuthMiddleware,
    SecurityHeadersMiddleware,
    CompressionMiddleware,
    CORSMiddleware,
    create_rate_limit_middleware,
    create_auth_middleware,
    create_logging_middleware,
    create_security_middleware,
)

# Convenience imports
from fastapi import FastAPI, APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware as FastAPICORSMiddleware

__all__ = [
    # Core
    "create_app",
    "create_pynext_app", 
    "PyNextApp",
    
    # Configuration
    "PyNextConfig",
    "get_config",
    "load_config",
    
    # Authentication
    "PasswordManager",
    "JWTManager", 
    "APIKeyManager",
    "AuthDependencies",
    "TokenResponse",
    "hash_password",
    "verify_password",
    "create_access_token",
    "create_refresh_token",
    "verify_token",
    "get_current_user",
    "get_current_active_user",
    "require_roles",
    "require_permissions",
    "generate_api_key",
    "generate_password",
    "create_token_response",
    "password_manager",
    "jwt_manager", 
    "api_key_manager",
    "auth_deps",
    
    # Middleware
    "PyNextMiddleware",
    "RequestLoggingMiddleware",
    "RateLimitMiddleware", 
    "AuthMiddleware",
    "SecurityHeadersMiddleware",
    "CompressionMiddleware",
    "CORSMiddleware",
    "create_rate_limit_middleware",
    "create_auth_middleware",
    "create_logging_middleware",
    "create_security_middleware",
    
    # FastAPI re-exports
    "FastAPI",
    "APIRouter", 
    "Depends",
    "HTTPException",
    "Request",
    "Response",
    "JSONResponse",
    "HTMLResponse",
    "FileResponse",
    "FastAPICORSMiddleware",
]