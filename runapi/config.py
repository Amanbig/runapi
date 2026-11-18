import os
from pathlib import Path
from typing import Annotated, Any, Dict, List, Optional

from pydantic import Field, ValidationError, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

from .errors import ConfigurationError


def _csv(value: Any) -> Any:
    """Split a comma-separated string into a list (env vars are plain strings)."""
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return value


class RunApiConfig(BaseSettings):
    """Typed configuration read from environment variables (and a ``.env`` file).

    Every field maps to the upper-case environment variable of the same name
    (``cors_origins`` -> ``CORS_ORIGINS``). Invalid values raise
    :class:`~runapi.errors.ConfigurationError` with a message naming the variable.
    Real environment variables take precedence over the ``.env`` file.
    """

    model_config = SettingsConfigDict(extra="ignore", validate_assignment=True)

    # Core settings
    environment: str = "development"
    debug: Optional[bool] = None  # defaults to True outside production
    host: str = "127.0.0.1"
    port: int = Field(8000, ge=1, le=65535)
    reload: bool = True

    # Security settings
    secret_key: str = "dev-secret-key-change-in-production"
    allowed_hosts: Annotated[List[str], NoDecode] = ["*"]

    # CORS settings (credentials are off by default: browsers reject "*" + credentials)
    cors_origins: Annotated[List[str], NoDecode] = ["*"]
    cors_credentials: bool = False
    cors_methods: Annotated[List[str], NoDecode] = ["*"]
    cors_headers: Annotated[List[str], NoDecode] = ["*"]

    # Database settings
    database_url: Optional[str] = None
    database_echo: bool = False

    # Cache settings
    cache_backend: str = "memory"  # "memory" or "redis" (rate limiting + token revocation)
    redis_url: Optional[str] = None
    cache_ttl: int = Field(300, ge=0)

    # Rate limiting
    rate_limit_enabled: bool = False
    rate_limit_calls: int = Field(100, ge=1)
    rate_limit_period: int = Field(60, ge=1)
    # Trust X-Forwarded-For for client IPs (enable only behind a proxy you control)
    trust_proxy_headers: bool = False

    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] %(message)s"
    log_json: Optional[bool] = None  # defaults to True in production

    # Static files
    static_files_enabled: bool = True
    static_files_path: str = "static"
    static_files_url: str = "/static"

    # Upload settings
    max_upload_size: int = Field(10 * 1024 * 1024, ge=0)  # 10MB
    upload_path: str = "uploads"

    # JWT settings
    jwt_algorithm: str = "HS256"
    jwt_expiry: int = Field(3600, ge=1)  # 1 hour
    jwt_refresh_expiry: int = Field(86400, ge=1)  # 24 hours

    # Operations
    health_enabled: bool = True
    # Fail startup when a route file cannot be imported (default: only in production)
    strict_routes: Optional[bool] = None

    # Custom settings
    custom: Dict[str, Any] = Field(default_factory=dict, exclude=True)

    def __init__(self, env_file: Optional[str] = None, **overrides: Any):
        self._load_env_file(env_file or ".env")
        try:
            super().__init__(**overrides)
        except ValidationError as exc:
            problems = "; ".join(
                f"{'.'.join(str(p).upper() for p in err['loc'])}: {err['msg']}"
                for err in exc.errors()
            )
            raise ConfigurationError(f"Invalid configuration: {problems}") from exc

    @field_validator("allowed_hosts", "cors_origins", "cors_methods", "cors_headers", mode="before")
    @classmethod
    def _split_csv(cls, value: Any) -> Any:
        return _csv(value)

    @field_validator("environment", "log_level", mode="after")
    @classmethod
    def _normalize(cls, value: str, info) -> str:
        return value.lower() if info.field_name == "environment" else value.upper()

    @model_validator(mode="after")
    def _apply_environment_defaults(self):
        production = self.environment == "production"
        # Bypass validate_assignment to avoid recursion while filling defaults
        if self.debug is None:
            object.__setattr__(self, "debug", not production)
        if self.log_json is None:
            object.__setattr__(self, "log_json", production)
        if self.strict_routes is None:
            object.__setattr__(self, "strict_routes", production)
        return self

    @staticmethod
    def _load_env_file(env_file: str) -> None:
        """Load a .env file into the environment without overriding real variables."""
        env_path = Path(env_file)
        if env_path.exists():
            with open(env_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Get custom configuration value."""
        return self.custom.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set custom configuration value."""
        self.custom[key] = value

    def is_development(self) -> bool:
        """Check if running in development mode."""
        return bool(self.debug)

    def is_production(self) -> bool:
        """Check if running in production mode (``ENVIRONMENT=production``)."""
        return self.environment == "production"

    def validate_settings(self) -> Dict[str, List[str]]:
        """Check the configuration for risky settings.

        Returns ``{"errors": [...], "warnings": [...]}``. Errors are only fatal in
        production, where the app refuses to start.
        """
        errors: List[str] = []
        warnings: List[str] = []

        if self.secret_key == "dev-secret-key-change-in-production":
            errors.append("SECRET_KEY is the default value; set a strong random secret")
        elif len(self.secret_key) < 32:
            warnings.append("SECRET_KEY is shorter than 32 characters")
        if "*" in self.cors_origins and self.cors_credentials:
            errors.append("CORS_ORIGINS='*' cannot be combined with CORS_CREDENTIALS=true")
        if self.is_production():
            if self.debug:
                errors.append("DEBUG is enabled in production")
            if "*" in self.cors_origins:
                warnings.append("CORS_ORIGINS allows every origin ('*')")
            if "*" in self.allowed_hosts:
                warnings.append("ALLOWED_HOSTS allows every host ('*')")
        return {"errors": errors, "warnings": warnings}


# Global configuration instance
config = RunApiConfig()


def get_config() -> RunApiConfig:
    """Get the global configuration instance."""
    return config


def load_config(env_file: Optional[str] = None) -> RunApiConfig:
    """Load configuration with optional custom env file."""
    global config
    config = RunApiConfig(env_file)
    return config
