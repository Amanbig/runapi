import os
from pathlib import Path
from typing import Any, Dict, List, Optional


class RunApiConfig:
    """Configuration management for RunApi framework."""

    def __init__(self, env_file: Optional[str] = None):
        self.env_file = env_file or ".env"
        self._load_env_file()

        # Core settings
        self.debug: bool = self._get_bool("DEBUG", True)
        self.host: str = self._get_str("HOST", "127.0.0.1")
        self.port: int = self._get_int("PORT", 8000)
        self.reload: bool = self._get_bool("RELOAD", True)

        # Security settings
        self.secret_key: str = self._get_str("SECRET_KEY", "dev-secret-key-change-in-production")
        self.allowed_hosts: List[str] = self._get_list("ALLOWED_HOSTS", ["*"])

        # CORS settings
        self.cors_origins: List[str] = self._get_list("CORS_ORIGINS", ["*"])
        self.cors_credentials: bool = self._get_bool("CORS_CREDENTIALS", True)
        self.cors_methods: List[str] = self._get_list("CORS_METHODS", ["*"])
        self.cors_headers: List[str] = self._get_list("CORS_HEADERS", ["*"])

        # Database settings
        self.database_url: Optional[str] = self._get_str("DATABASE_URL")
        self.database_echo: bool = self._get_bool("DATABASE_ECHO", False)

        # Cache settings
        self.cache_backend: str = self._get_str("CACHE_BACKEND", "memory")
        self.redis_url: Optional[str] = self._get_str("REDIS_URL")
        self.cache_ttl: int = self._get_int("CACHE_TTL", 300)  # 5 minutes default

        # Rate limiting
        self.rate_limit_enabled: bool = self._get_bool("RATE_LIMIT_ENABLED", False)
        self.rate_limit_calls: int = self._get_int("RATE_LIMIT_CALLS", 100)
        self.rate_limit_period: int = self._get_int("RATE_LIMIT_PERIOD", 60)  # 1 minute

        # Logging
        self.log_level: str = self._get_str("LOG_LEVEL", "INFO")
        self.log_format: str = self._get_str(
            "LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Static files
        self.static_files_enabled: bool = self._get_bool("STATIC_FILES_ENABLED", True)
        self.static_files_path: str = self._get_str("STATIC_FILES_PATH", "static")
        self.static_files_url: str = self._get_str("STATIC_FILES_URL", "/static")

        # Upload settings
        self.max_upload_size: int = self._get_int("MAX_UPLOAD_SIZE", 10 * 1024 * 1024)  # 10MB
        self.upload_path: str = self._get_str("UPLOAD_PATH", "uploads")

        # JWT settings
        self.jwt_algorithm: str = self._get_str("JWT_ALGORITHM", "HS256")
        self.jwt_expiry: int = self._get_int("JWT_EXPIRY", 3600)  # 1 hour
        self.jwt_refresh_expiry: int = self._get_int("JWT_REFRESH_EXPIRY", 86400)  # 24 hours

        # Custom settings
        self.custom: Dict[str, Any] = {}

    def _load_env_file(self):
        """Load environment variables from .env file if it exists."""
        env_path = Path(self.env_file)
        if env_path.exists():
            with open(env_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        os.environ[key] = value

    def _get_str(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get string value from environment."""
        return os.getenv(key, default)

    def _get_bool(self, key: str, default: bool = False) -> bool:
        """Get boolean value from environment."""
        value = os.getenv(key, str(default)).lower()
        return value in ("true", "1", "yes", "on")

    def _get_int(self, key: str, default: int = 0) -> int:
        """Get integer value from environment."""
        try:
            return int(os.getenv(key, str(default)))
        except ValueError:
            return default

    def _get_float(self, key: str, default: float = 0.0) -> float:
        """Get float value from environment."""
        try:
            return float(os.getenv(key, str(default)))
        except ValueError:
            return default

    def _get_list(self, key: str, default: List[str] = None) -> List[str]:
        """Get list value from environment (comma-separated)."""
        if default is None:
            default = []

        value = os.getenv(key)
        if not value:
            return default

        return [item.strip() for item in value.split(",") if item.strip()]

    def get(self, key: str, default: Any = None) -> Any:
        """Get custom configuration value."""
        return self.custom.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set custom configuration value."""
        self.custom[key] = value

    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.debug

    def is_production(self) -> bool:
        """Check if running in production mode."""
        return not self.debug


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
