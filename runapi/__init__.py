"""
RunApi - A Next.js-inspired file-based routing framework built on FastAPI
"""

__version__ = "0.1.3"
__author__ = "Amanpreet Singh"
__email__ = "amanpreetsinghjhiwant7@gmail.com"

# Core framework
# Authentication
from .auth import (
    APIKeyManager,
    AuthDependencies,
    JWTManager,
    PasswordManager,
    TokenResponse,
    api_key_manager,
    create_access_token,
    create_refresh_token,
    create_token_response,
    generate_api_key,
    generate_password,
    get_current_active_user,
    get_current_user,
    hash_password,
    require_permissions,
    require_roles,
    verify_password,
    verify_token,
)

# Configuration
from .config import RunApiConfig, get_config, load_config
from .core import RunApiApp, create_app, create_runapi_app

# Error handling
from .errors import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    DatabaseError,
    ErrorHandler,
    ErrorResponse,
    ExternalServiceError,
    NotFoundError,
    RateLimitError,
    RunApiException,
    ServerError,
    ValidationError,
    bad_request,
    conflict,
    create_error_response,
    forbidden,
    internal_error,
    not_found,
    raise_auth_error,
    raise_conflict,
    raise_not_found,
    raise_permission_error,
    raise_server_error,
    raise_validation_error,
    rate_limited,
    setup_error_handlers,
    unauthorized,
    unprocessable_entity,
)

# Middleware
from .middleware import (
    AuthMiddleware,
    CompressionMiddleware,
    CORSMiddleware,
    RateLimitMiddleware,
    RequestLoggingMiddleware,
    RunApiMiddleware,
    SecurityHeadersMiddleware,
    create_auth_middleware,
    create_logging_middleware,
    create_rate_limit_middleware,
    create_security_middleware,
)

# Repository
from .repository import (
    SQLALCHEMY_AVAILABLE,
    BaseRepository,
    InMemoryRepository,
    RepositoryFactory,
    RepositoryProtocol,
    TypedInMemoryRepository,
    create_repository,
)

# Schemas
from .schemas import (
    BaseSchema,
    ErrorDetail,
    IDMixin,
    MessageResponse,
    PaginatedResponse,
    PaginationParams,
    SchemaRegistry,
    TimestampMixin,
    create_create_model,
    create_response_model,
    create_update_model,
    get_schema,
    list_schemas,
    load_schemas,
)
from .schemas import (
    ErrorResponse as SchemaErrorResponse,
)

# Conditional SQLAlchemy import
if SQLALCHEMY_AVAILABLE:
    from .repository import SQLAlchemyRepository
else:
    SQLAlchemyRepository = None  # type: ignore

# Service
# Convenience imports
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware as FastAPICORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

from .service import (
    BaseService,
    CRUDService,
    ServiceFactory,
    ValidatedService,
    create_crud_service,
    create_service_dependency,
    log_operation,
    require_exists,
    validate_input,
)

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
