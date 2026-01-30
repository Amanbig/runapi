"""
RunApi - A Next.js-inspired file-based routing framework built on FastAPI
"""

__version__ = "0.1.3"
__author__ = "Amanpreet Singh"
__email__ = "amanpreetsinghjhiwant7@gmail.com"

# Core framework
from .core import create_app, create_runapi_app, RunApiApp

# Configuration
from .config import RunApiConfig, get_config, load_config

# Error handling
from .errors import (
    RunApiException,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ConflictError,
    RateLimitError,
    ServerError,
    DatabaseError,
    ExternalServiceError,
    ErrorResponse,
    ErrorHandler,
    setup_error_handlers,
    raise_validation_error,
    raise_auth_error,
    raise_permission_error,
    raise_not_found,
    raise_conflict,
    raise_server_error,
    create_error_response,
    bad_request,
    unauthorized,
    forbidden,
    not_found,
    conflict,
    unprocessable_entity,
    rate_limited,
    internal_error,
)

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
    api_key_manager,
)

# Middleware
from .middleware import (
    RunApiMiddleware,
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

# Schemas
from .schemas import (
    BaseSchema,
    TimestampMixin,
    IDMixin,
    MessageResponse,
    PaginatedResponse,
    PaginationParams,
    ErrorDetail,
    ErrorResponse as SchemaErrorResponse,
    SchemaRegistry,
    load_schemas,
    get_schema,
    list_schemas,
    create_response_model,
    create_create_model,
    create_update_model,
)

# Repository
from .repository import (
    BaseRepository,
    RepositoryProtocol,
    InMemoryRepository,
    TypedInMemoryRepository,
    RepositoryFactory,
    create_repository,
    SQLALCHEMY_AVAILABLE,
)

# Conditional SQLAlchemy import
if SQLALCHEMY_AVAILABLE:
    from .repository import SQLAlchemyRepository
else:
    SQLAlchemyRepository = None  # type: ignore

# Service
from .service import (
    BaseService,
    CRUDService,
    ValidatedService,
    ServiceFactory,
    validate_input,
    require_exists,
    log_operation,
    create_service_dependency,
    create_crud_service,
)

# Convenience imports
from fastapi import FastAPI, APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware as FastAPICORSMiddleware

__all__ = [
    # Core
    "create_app",
    "create_runapi_app", 
    "RunApiApp",
    
    # Configuration
    "RunApiConfig",
    "get_config",
    "load_config",
    
    # Error handling
    "RunApiException",
    "ValidationError",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "ConflictError",
    "RateLimitError",
    "ServerError",
    "DatabaseError",
    "ExternalServiceError",
    "ErrorResponse",
    "ErrorHandler",
    "setup_error_handlers",
    "raise_validation_error",
    "raise_auth_error",
    "raise_permission_error",
    "raise_not_found",
    "raise_conflict",
    "raise_server_error",
    "create_error_response",
    "bad_request",
    "unauthorized",
    "forbidden",
    "not_found",
    "conflict",
    "unprocessable_entity",
    "rate_limited",
    "internal_error",
    
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
    "api_key_manager",
    
    # Middleware
    "RunApiMiddleware",
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
    
    # Schemas
    "BaseSchema",
    "TimestampMixin",
    "IDMixin",
    "MessageResponse",
    "PaginatedResponse",
    "PaginationParams",
    "ErrorDetail",
    "SchemaErrorResponse",
    "SchemaRegistry",
    "load_schemas",
    "get_schema",
    "list_schemas",
    "create_response_model",
    "create_create_model",
    "create_update_model",

    # Repository
    "BaseRepository",
    "RepositoryProtocol",
    "InMemoryRepository",
    "TypedInMemoryRepository",
    "SQLAlchemyRepository",
    "RepositoryFactory",
    "create_repository",
    "SQLALCHEMY_AVAILABLE",

    # Service
    "BaseService",
    "CRUDService",
    "ValidatedService",
    "ServiceFactory",
    "validate_input",
    "require_exists",
    "log_operation",
    "create_service_dependency",
    "create_crud_service",

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