"""Structured logging helpers: JSON formatter and per-request correlation IDs."""

import json
import logging
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

request_id_var: ContextVar[Optional[str]] = ContextVar("runapi_request_id", default=None)

REQUEST_ID_HEADER = "X-Request-ID"

_STANDARD_ATTRS = set(logging.LogRecord("", 0, "", 0, "", (), None).__dict__) | {
    "message",
    "asctime",
    "request_id",
}


def get_request_id() -> Optional[str]:
    """Return the current request's correlation ID (or None outside a request)."""
    return request_id_var.get()


class RequestIDFilter(logging.Filter):
    """Attach the current request ID to every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get() or "-"
        return True


class JSONFormatter(logging.Formatter):
    """Format log records as one JSON object per line."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        request_id = getattr(record, "request_id", None) or request_id_var.get()
        if request_id and request_id != "-":
            payload["request_id"] = request_id
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        for key, value in record.__dict__.items():
            if key not in _STANDARD_ATTRS and not key.startswith("_"):
                payload[key] = value
        return json.dumps(payload, default=str)


def configure_logging(level: str = "INFO", json_logs: bool = False, text_format: str = None):
    """Configure the root logger (idempotent: replaces handlers it previously installed)."""
    root = logging.getLogger()
    for handler in list(root.handlers):
        if getattr(handler, "_runapi", False):
            root.removeHandler(handler)

    handler = logging.StreamHandler()
    handler._runapi = True  # type: ignore[attr-defined]
    handler.addFilter(RequestIDFilter())
    if json_logs:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                text_format
                or "%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] %(message)s"
            )
        )
    root.addHandler(handler)
    root.setLevel(getattr(logging, level.upper(), logging.INFO))


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Read or generate an ``X-Request-ID`` and expose it to logs and the response."""

    async def dispatch(self, request: Request, call_next):
        incoming = request.headers.get(REQUEST_ID_HEADER, "")
        # Accept a client-supplied ID only if it is short and printable
        request_id = incoming if 0 < len(incoming) <= 128 and incoming.isprintable() else None
        request_id = request_id or uuid.uuid4().hex
        request.state.request_id = request_id
        token = request_id_var.set(request_id)
        try:
            response = await call_next(request)
        finally:
            request_id_var.reset(token)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response
