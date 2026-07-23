"""
Configuration management for ZainJo LogStream.
Reads settings from config.yaml and environment variables.
"""
import os
import yaml
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings


def _load_yaml_config() -> dict:
    """Load configuration from config.yaml if it exists."""
    config_path = os.environ.get("CONFIG_PATH", "/etc/zainjo-logstream/config.yaml")
    alt_paths = [
        config_path,
        Path(__file__).parent.parent.parent / "config.yaml",
        Path.cwd() / "config.yaml",
    ]
    for path in alt_paths:
        p = Path(path)
        if p.exists():
            with open(p) as f:
                return yaml.safe_load(f) or {}
    return {}


_yaml = _load_yaml_config()


class Settings(BaseSettings):
    # Application
    app_name: str = "ZainJo LogStream"
    app_version: str = "1.0.0"
    debug: bool = False

    # API server
    api_host: str = Field(default_factory=lambda: _yaml.get("api_host", "0.0.0.0"))
    api_port: int = Field(default_factory=lambda: _yaml.get("api_port", 8080))

    # Syslog listener
    syslog_host: str = Field(default_factory=lambda: _yaml.get("syslog_host", "0.0.0.0"))
    syslog_port: int = Field(default_factory=lambda: _yaml.get("syslog_port", 1514))
    syslog_tcp_enabled: bool = Field(default_factory=lambda: _yaml.get("syslog_tcp_enabled", True))
    syslog_udp_enabled: bool = Field(default_factory=lambda: _yaml.get("syslog_udp_enabled", True))
    syslog_buffer_size: int = Field(default_factory=lambda: _yaml.get("syslog_buffer_size", 65535))
    syslog_queue_size: int = Field(default_factory=lambda: _yaml.get("syslog_queue_size", 100000))
    syslog_workers: int = Field(default_factory=lambda: _yaml.get("syslog_workers", 8))

    # Database
    database_url: str = Field(
        default_factory=lambda: _yaml.get(
            "database_url",
            os.environ.get("DATABASE_URL", "postgresql+asyncpg://logstream:changeme@localhost:5432/logstream")
        )
    )

    # Storage
    storage_path: str = Field(default_factory=lambda: _yaml.get("storage_path", "/data/syslog"))
    retention_days: int = Field(default_factory=lambda: _yaml.get("retention_days", 90))
    compress_after_days: int = Field(default_factory=lambda: _yaml.get("compress_after_days", 7))

    # SIEM integration
    siem_url: str = Field(default_factory=lambda: _yaml.get("siem_url", "http://localhost:5000/api/logs"))
    siem_enabled: bool = Field(default_factory=lambda: _yaml.get("siem_enabled", True))
    siem_timeout: int = Field(default_factory=lambda: _yaml.get("siem_timeout", 10))
    siem_retry_attempts: int = Field(default_factory=lambda: _yaml.get("siem_retry_attempts", 3))
    siem_retry_delay: float = Field(default_factory=lambda: _yaml.get("siem_retry_delay", 2.0))
    siem_batch_size: int = Field(default_factory=lambda: _yaml.get("siem_batch_size", 100))

    # Authentication
    secret_key: str = Field(
        default_factory=lambda: _yaml.get(
            "secret_key",
            os.environ.get("SECRET_KEY", "CHANGE-THIS-SECRET-KEY-IN-PRODUCTION")
        )
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(
        default_factory=lambda: _yaml.get("access_token_expire_minutes", 480)
    )

    # Cleanup scheduler
    cleanup_interval_hours: int = Field(default_factory=lambda: _yaml.get("cleanup_interval_hours", 24))

    # Logging
    log_level: str = Field(default_factory=lambda: _yaml.get("log_level", "INFO"))
    log_file: str = Field(default_factory=lambda: _yaml.get("log_file", "/var/log/zainjo-logstream/app.log"))

    class Config:
        env_prefix = "LOGSTREAM_"
        env_file = ".env"
        extra = "ignore"


settings = Settings()
