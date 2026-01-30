"""
Error handling system for RunApi framework
"""

import logging
import traceback
from typing import Any, Dict, Optional

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class RunApiException(Exception):
    """Base exception class for RunApi framework."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        self.error_code = error_code or self.__class__.__name__
        super().__init__(self.message)


class ValidationError(RunApiException):
    """Raised when request validation fails."""

    def __init__(self, message: str = "Validation failed", details: Dict[str, Any] = None):
        super().__init__(message, 400, details, "VALIDATION_ERROR")


class AuthenticationError(RunApiException):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication required", details: Dict[str, Any] = None):
        super().__init__(message, 401, details, "AUTHENTICATION_ERROR")


class AuthorizationError(RunApiException):
    """Raised when authorization fails."""

    def __init__(self, message: str = "Insufficient permissions", details: Dict[str, Any] = None):
        super().__init__(message, 403, details, "AUTHORIZATION_ERROR")


class NotFoundError(RunApiException):
    """Raised when a resource is not found."""

    def __init__(self, message: str = "Resource not found", details: Dict[str, Any] = None):
        super().__init__(message, 404, details, "NOT_FOUND_ERROR")


class ConflictError(RunApiException):
    """Raised when there's a conflict with the current state."""

    def __init__(
        self, message: str = "Conflict with current state", details: Dict[str, Any] = None
    ):
        super().__init__(message, 409, details, "CONFLICT_ERROR")


class RateLimitError(RunApiException):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str = "Rate limit exceeded", details: Dict[str, Any] = None):
        super().__init__(message, 429, details, "RATE_LIMIT_ERROR")


class ServerError(RunApiException):
    """Raised when an internal server error occurs."""

    def __init__(self, message: str = "Internal server error", details: Dict[str, Any] = None):
        super().__init__(message, 500, details, "SERVER_ERROR")


class DatabaseError(RunApiException):
    """Raised when database operations fail."""

    def __init__(self, message: str = "Database operation failed", details: Dict[str, Any] = None):
        super().__init__(message, 500, details, "DATABASE_ERROR")


class ExternalServiceError(RunApiException):
    """Raised when external service calls fail."""

    def __init__(self, message: str = "External service error", details: Dict[str, Any] = None):
        super().__init__(message, 502, details, "EXTERNAL_SERVICE_ERROR")


class ErrorResponse:
    """Standard error response format."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "UNKNOWN_ERROR",
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        self.request_id = request_id

    def to_dict(self) -> Dict[str, Any]:
        """Convert error response to dictionary."""
        response = {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "status_code": self.status_code,
            }
        }

        if self.details:
            response["error"]["details"] = self.details

        if self.request_id:
            response["error"]["request_id"] = self.request_id

        return response

    def to_json_response(self) -> JSONResponse:
        """Convert to FastAPI JSONResponse."""
        return JSONResponse(status_code=self.status_code, content=self.to_dict())


class ErrorHandler:
    """Error handler with logging and formatting."""

    def __init__(self, logger: Optional[logging.Logger] = None, debug: bool = False):
        self.logger = logger or logging.getLogger(__name__)
        self.debug = debug

    def handle_runapi_exception(self, request: Request, exc: RunApiException) -> JSONResponse:
        """Handle RunApi custom exceptions."""
        self.logger.warning(
            f"RunApi exception: {exc.error_code} - {exc.message}",
            extra={"status_code": exc.status_code, "details": exc.details},
        )

        error_response = ErrorResponse(
            message=exc.message,
            status_code=exc.status_code,
            error_code=exc.error_code,
            details=exc.details,
            request_id=getattr(request.state, "request_id", None),
        )

        return error_response.to_json_response()

    def handle_http_exception(self, request: Request, exc: HTTPException) -> JSONResponse:
        """Handle FastAPI HTTP exceptions."""
        self.logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")

        error_response = ErrorResponse(
            message=str(exc.detail),
            status_code=exc.status_code,
            error_code="HTTP_ERROR",
            request_id=getattr(request.state, "request_id", None),
        )

        return error_response.to_json_response()

    def handle_validation_exception(self, request: Request, exc: Exception) -> JSONResponse:
        """Handle Pydantic validation exceptions."""
        self.logger.warning(f"Validation exception: {str(exc)}")

        details = {}
        if hasattr(exc, "errors"):
            details = {"validation_errors": exc.errors()}

        error_response = ErrorResponse(
            message="Request validation failed",
            status_code=422,
            error_code="VALIDATION_ERROR",
            details=details,
            request_id=getattr(request.state, "request_id", None),
        )

        return error_response.to_json_response()

    def handle_generic_exception(self, request: Request, exc: Exception) -> JSONResponse:
        """Handle generic exceptions."""
        self.logger.error(f"Unhandled exception: {type(exc).__name__} - {str(exc)}", exc_info=True)

        details = {}
        if self.debug:
            details = {
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
                "traceback": traceback.format_exc().split("\n"),
            }

        error_response = ErrorResponse(
            message="An unexpected error occurred" if not self.debug else str(exc),
            status_code=500,
            error_code="INTERNAL_ERROR",
            details=details,
            request_id=getattr(request.state, "request_id", None),
        )

        return error_response.to_json_response()


# Global error handler instance
error_handler = ErrorHandler()


def setup_error_handlers(app, logger: Optional[logging.Logger] = None, debug: bool = False):
    """Setup error handlers for a FastAPI application."""
    handler = ErrorHandler(logger, debug)

    @app.exception_handler(RunApiException)
    async def runapi_exception_handler(request: Request, exc: RunApiException):
        return handler.handle_runapi_exception(request, exc)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return handler.handle_http_exception(request, exc)

    @app.exception_handler(StarletteHTTPException)
    async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException):
        return handler.handle_http_exception(
            request, HTTPException(status_code=exc.status_code, detail=exc.detail)
        )

    # Handle validation errors from Pydantic
    try:
        from pydantic import ValidationError as PydanticValidationError

        @app.exception_handler(PydanticValidationError)
        async def pydantic_validation_exception_handler(
            request: Request, exc: PydanticValidationError
        ):
            return handler.handle_validation_exception(request, exc)
    except ImportError:
        pass

    # Handle generic exceptions
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        return handler.handle_generic_exception(request, exc)


# Convenience functions
def raise_validation_error(message: str, details: Dict[str, Any] = None):
    """Raise a validation error."""
    raise ValidationError(message, details)


def raise_auth_error(message: str = "Authentication required"):
    """Raise an authentication error."""
    raise AuthenticationError(message)


def raise_permission_error(message: str = "Insufficient permissions"):
    """Raise an authorization error."""
    raise AuthorizationError(message)


def raise_not_found(message: str = "Resource not found"):
    """Raise a not found error."""
    raise NotFoundError(message)


def raise_conflict(message: str = "Conflict with current state"):
    """Raise a conflict error."""
    raise ConflictError(message)


def raise_server_error(message: str = "Internal server error"):
    """Raise a server error."""
    raise ServerError(message)


def create_error_response(
    message: str, status_code: int = 500, error_code: str = "ERROR", details: Dict[str, Any] = None
) -> JSONResponse:
    """Create a standard error response."""
    error_response = ErrorResponse(
        message=message, status_code=status_code, error_code=error_code, details=details
    )
    return error_response.to_json_response()


# HTTP status code helpers
def bad_request(message: str = "Bad request", details: Dict[str, Any] = None) -> JSONResponse:
    """Return a 400 Bad Request response."""
    return create_error_response(message, 400, "BAD_REQUEST", details)


def unauthorized(message: str = "Unauthorized", details: Dict[str, Any] = None) -> JSONResponse:
    """Return a 401 Unauthorized response."""
    return create_error_response(message, 401, "UNAUTHORIZED", details)


def forbidden(message: str = "Forbidden", details: Dict[str, Any] = None) -> JSONResponse:
    """Return a 403 Forbidden response."""
    return create_error_response(message, 403, "FORBIDDEN", details)


def not_found(message: str = "Not found", details: Dict[str, Any] = None) -> JSONResponse:
    """Return a 404 Not Found response."""
    return create_error_response(message, 404, "NOT_FOUND", details)


def conflict(message: str = "Conflict", details: Dict[str, Any] = None) -> JSONResponse:
    """Return a 409 Conflict response."""
    return create_error_response(message, 409, "CONFLICT", details)


def unprocessable_entity(
    message: str = "Unprocessable Entity", details: Dict[str, Any] = None
) -> JSONResponse:
    """Return a 422 Unprocessable Entity response."""
    return create_error_response(message, 422, "UNPROCESSABLE_ENTITY", details)


def rate_limited(
    message: str = "Rate limit exceeded", details: Dict[str, Any] = None
) -> JSONResponse:
    """Return a 429 Too Many Requests response."""
    return create_error_response(message, 429, "RATE_LIMITED", details)


def internal_error(
    message: str = "Internal server error", details: Dict[str, Any] = None
) -> JSONResponse:
    """Return a 500 Internal Server Error response."""
    return create_error_response(message, 500, "INTERNAL_ERROR", details)
