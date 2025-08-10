"""
Unified configuration system for the consolidated authentication service.

This module provides comprehensive configuration options for different
authentication modes, replacing the fragmented configuration across
multiple auth services.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover - yaml is optional
    yaml = None


def _env_bool(value: Optional[str], default: bool) -> bool:
    """Convert environment string to boolean with a default."""
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def _env_int(value: Optional[str], default: int) -> int:
    """Convert environment string to integer with a default."""
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def _env_float(value: Optional[str], default: float) -> float:
    """Convert environment string to float with a default."""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def _load_env_file(file_path: Union[str, Path]) -> None:
    """Simple .env file parser that updates os.environ."""
    for line in Path(file_path).read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


@dataclass
class DatabaseConfig:
    """Database connection and settings configuration."""

    database_url: str = "postgresql+asyncpg://karen_user:karen_secure_pass_change_me@localhost:5432/ai_karen"
    connection_pool_size: int = 10
    connection_pool_max_overflow: int = 20
    connection_timeout_seconds: int = 30
    query_timeout_seconds: int = 30
    enable_query_logging: bool = False

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Create configuration from environment variables."""
        # Use PostgreSQL environment variables with fallbacks
        database_url = (
            os.getenv("AUTH_DATABASE_URL") or 
            os.getenv("POSTGRES_URL") or 
            os.getenv("DATABASE_URL") or 
            cls().database_url
        )
        
        # Ensure async driver is used for PostgreSQL
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        
        return cls(
            database_url=database_url,
            connection_pool_size=_env_int(
                os.getenv("AUTH_DB_POOL_SIZE"), cls().connection_pool_size
            ),
            connection_pool_max_overflow=_env_int(
                os.getenv("AUTH_DB_POOL_MAX_OVERFLOW"),
                cls().connection_pool_max_overflow,
            ),
            connection_timeout_seconds=_env_int(
                os.getenv("AUTH_DB_CONNECTION_TIMEOUT"),
                cls().connection_timeout_seconds,
            ),
            query_timeout_seconds=_env_int(
                os.getenv("AUTH_DB_QUERY_TIMEOUT"), cls().query_timeout_seconds
            ),
            enable_query_logging=_env_bool(
                os.getenv("AUTH_DB_ENABLE_QUERY_LOGGING"), cls().enable_query_logging
            ),
        )


@dataclass
class JWTConfig:
    """JWT token configuration for access and refresh tokens."""

    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30
    password_reset_token_expire_hours: int = 1
    email_verification_token_expire_hours: int = 24

    @classmethod
    def from_env(cls) -> "JWTConfig":
        """Create configuration from environment variables."""
        return cls(
            secret_key=os.getenv("AUTH_SECRET_KEY", cls().secret_key),
            algorithm=os.getenv("AUTH_JWT_ALGORITHM", cls().algorithm),
            access_token_expire_minutes=_env_int(
                os.getenv("AUTH_ACCESS_TOKEN_EXPIRE_MINUTES"),
                cls().access_token_expire_minutes,
            ),
            refresh_token_expire_days=_env_int(
                os.getenv("AUTH_REFRESH_TOKEN_EXPIRE_DAYS"),
                cls().refresh_token_expire_days,
            ),
            password_reset_token_expire_hours=_env_int(
                os.getenv("AUTH_PASSWORD_RESET_TOKEN_EXPIRE_HOURS"),
                cls().password_reset_token_expire_hours,
            ),
            email_verification_token_expire_hours=_env_int(
                os.getenv("AUTH_EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS"),
                cls().email_verification_token_expire_hours,
            ),
        )

    @property
    def access_token_expiry(self) -> timedelta:
        """Get access token expiry as timedelta."""
        return timedelta(minutes=self.access_token_expire_minutes)

    @property
    def refresh_token_expiry(self) -> timedelta:
        """Get refresh token expiry as timedelta."""
        return timedelta(days=self.refresh_token_expire_days)

    @property
    def password_reset_token_expiry(self) -> timedelta:
        """Get password reset token expiry as timedelta."""
        return timedelta(hours=self.password_reset_token_expire_hours)

    @property
    def email_verification_token_expiry(self) -> timedelta:
        """Get email verification token expiry as timedelta."""
        return timedelta(hours=self.email_verification_token_expire_hours)


@dataclass
class SessionConfig:
    """Session management configuration."""

    session_timeout_hours: int = 24
    max_sessions_per_user: int = 5
    storage_type: str = "database"  # "database" (PostgreSQL), "redis", "memory"
    redis_url: Optional[str] = None
    cookie_name: str = "auth_session"
    cookie_secure: bool = True
    cookie_httponly: bool = True
    cookie_samesite: str = "lax"  # "strict", "lax", "none"

    @classmethod
    def from_env(cls) -> "SessionConfig":
        """Create configuration from environment variables."""
        return cls(
            session_timeout_hours=_env_int(
                os.getenv("AUTH_SESSION_TIMEOUT_HOURS"), cls().session_timeout_hours
            ),
            max_sessions_per_user=_env_int(
                os.getenv("AUTH_MAX_SESSIONS_PER_USER"), cls().max_sessions_per_user
            ),
            storage_type=os.getenv("AUTH_SESSION_STORAGE_TYPE", cls().storage_type),
            redis_url=os.getenv("AUTH_SESSION_REDIS_URL") or os.getenv("REDIS_URL"),
            cookie_name=os.getenv("AUTH_SESSION_COOKIE_NAME", cls().cookie_name),
            cookie_secure=_env_bool(
                os.getenv("AUTH_SESSION_COOKIE_SECURE"), cls().cookie_secure
            ),
            cookie_httponly=_env_bool(
                os.getenv("AUTH_SESSION_COOKIE_HTTPONLY"), cls().cookie_httponly
            ),
            cookie_samesite=os.getenv(
                "AUTH_SESSION_COOKIE_SAMESITE", cls().cookie_samesite
            ),
        )

    @property
    def session_timeout(self) -> timedelta:
        """Get session timeout as timedelta."""
        return timedelta(hours=self.session_timeout_hours)


@dataclass
class SecurityConfig:
    """Security enhancement configuration."""

    # Rate limiting
    enable_rate_limiting: bool = True
    max_failed_attempts: int = 5
    lockout_duration_minutes: int = 15
    rate_limit_window_minutes: int = 15
    rate_limit_max_requests: int = 10
    rate_limit_storage: str = "memory"  # "memory" or "redis"
    rate_limit_redis_url: Optional[str] = None

    # Password security
    min_password_length: int = 8
    require_password_complexity: bool = True
    password_hash_rounds: int = 12
    password_hash_algorithm: str = "bcrypt"  # "bcrypt" or "argon2"

    # Session security
    enable_session_validation: bool = True
    validate_ip_address: bool = False
    validate_user_agent: bool = False
    enable_device_fingerprinting: bool = False

    # Audit logging
    enable_audit_logging: bool = True
    log_successful_logins: bool = True
    log_failed_logins: bool = True
    log_security_events: bool = True

    @classmethod
    def from_env(cls) -> "SecurityConfig":
        """Create configuration from environment variables."""
        return cls(
            enable_rate_limiting=_env_bool(
                os.getenv("AUTH_ENABLE_RATE_LIMITING"), cls().enable_rate_limiting
            ),
            max_failed_attempts=_env_int(
                os.getenv("AUTH_MAX_FAILED_ATTEMPTS"), cls().max_failed_attempts
            ),
            lockout_duration_minutes=_env_int(
                os.getenv("AUTH_LOCKOUT_DURATION_MINUTES"),
                cls().lockout_duration_minutes,
            ),
            rate_limit_window_minutes=_env_int(
                os.getenv("AUTH_RATE_LIMIT_WINDOW_MINUTES"),
                cls().rate_limit_window_minutes,
            ),
            rate_limit_max_requests=_env_int(
                os.getenv("AUTH_RATE_LIMIT_MAX_REQUESTS"), cls().rate_limit_max_requests
            ),
            rate_limit_storage=os.getenv(
                "AUTH_RATE_LIMIT_STORAGE", cls().rate_limit_storage
            ),
            rate_limit_redis_url=(
                os.getenv("AUTH_RATE_LIMIT_REDIS_URL")
                or os.getenv("REDIS_URL")
            ),
            min_password_length=_env_int(
                os.getenv("AUTH_MIN_PASSWORD_LENGTH"), cls().min_password_length
            ),
            require_password_complexity=_env_bool(
                os.getenv("AUTH_REQUIRE_PASSWORD_COMPLEXITY"),
                cls().require_password_complexity,
            ),
            password_hash_rounds=_env_int(
                os.getenv("AUTH_PASSWORD_HASH_ROUNDS"), cls().password_hash_rounds
            ),
            password_hash_algorithm=os.getenv(
                "AUTH_PASSWORD_HASH_ALGORITHM", cls().password_hash_algorithm
            ),
            enable_session_validation=_env_bool(
                os.getenv("AUTH_ENABLE_SESSION_VALIDATION"),
                cls().enable_session_validation,
            ),
            validate_ip_address=_env_bool(
                os.getenv("AUTH_VALIDATE_IP_ADDRESS"), cls().validate_ip_address
            ),
            validate_user_agent=_env_bool(
                os.getenv("AUTH_VALIDATE_USER_AGENT"), cls().validate_user_agent
            ),
            enable_device_fingerprinting=_env_bool(
                os.getenv("AUTH_ENABLE_DEVICE_FINGERPRINTING"),
                cls().enable_device_fingerprinting,
            ),
            enable_audit_logging=_env_bool(
                os.getenv("AUTH_ENABLE_AUDIT_LOGGING"), cls().enable_audit_logging
            ),
            log_successful_logins=_env_bool(
                os.getenv("AUTH_LOG_SUCCESSFUL_LOGINS"), cls().log_successful_logins
            ),
            log_failed_logins=_env_bool(
                os.getenv("AUTH_LOG_FAILED_LOGINS"), cls().log_failed_logins
            ),
            log_security_events=_env_bool(
                os.getenv("AUTH_LOG_SECURITY_EVENTS"), cls().log_security_events
            ),
        )


@dataclass
class IntelligenceConfig:
    """Intelligence layer configuration for advanced authentication features."""

    # Feature toggles
    enable_intelligent_auth: bool = False
    enable_anomaly_detection: bool = False
    enable_behavioral_analysis: bool = False
    enable_threat_detection: bool = False

    # Risk scoring
    risk_threshold_low: float = 0.3
    risk_threshold_medium: float = 0.6
    risk_threshold_high: float = 0.8

    # ML model settings
    model_update_interval_hours: int = 24
    min_training_samples: int = 100
    enable_online_learning: bool = False

    # Behavioral analysis
    behavioral_window_days: int = 30
    location_sensitivity: float = 0.5
    time_sensitivity: float = 0.3
    device_sensitivity: float = 0.7

    @classmethod
    def from_env(cls) -> "IntelligenceConfig":
        """Create configuration from environment variables."""
        return cls(
            enable_intelligent_auth=_env_bool(
                os.getenv("AUTH_ENABLE_INTELLIGENT_AUTH"), cls().enable_intelligent_auth
            ),
            enable_anomaly_detection=_env_bool(
                os.getenv("AUTH_ENABLE_ANOMALY_DETECTION"),
                cls().enable_anomaly_detection,
            ),
            enable_behavioral_analysis=_env_bool(
                os.getenv("AUTH_ENABLE_BEHAVIORAL_ANALYSIS"),
                cls().enable_behavioral_analysis,
            ),
            enable_threat_detection=_env_bool(
                os.getenv("AUTH_ENABLE_THREAT_DETECTION"), cls().enable_threat_detection
            ),
            risk_threshold_low=_env_float(
                os.getenv("AUTH_RISK_THRESHOLD_LOW"), cls().risk_threshold_low
            ),
            risk_threshold_medium=_env_float(
                os.getenv("AUTH_RISK_THRESHOLD_MEDIUM"), cls().risk_threshold_medium
            ),
            risk_threshold_high=_env_float(
                os.getenv("AUTH_RISK_THRESHOLD_HIGH"), cls().risk_threshold_high
            ),
            model_update_interval_hours=_env_int(
                os.getenv("AUTH_MODEL_UPDATE_INTERVAL_HOURS"),
                cls().model_update_interval_hours,
            ),
            min_training_samples=_env_int(
                os.getenv("AUTH_MIN_TRAINING_SAMPLES"), cls().min_training_samples
            ),
            enable_online_learning=_env_bool(
                os.getenv("AUTH_ENABLE_ONLINE_LEARNING"), cls().enable_online_learning
            ),
            behavioral_window_days=_env_int(
                os.getenv("AUTH_BEHAVIORAL_WINDOW_DAYS"), cls().behavioral_window_days
            ),
            location_sensitivity=_env_float(
                os.getenv("AUTH_LOCATION_SENSITIVITY"), cls().location_sensitivity
            ),
            time_sensitivity=_env_float(
                os.getenv("AUTH_TIME_SENSITIVITY"), cls().time_sensitivity
            ),
            device_sensitivity=_env_float(
                os.getenv("AUTH_DEVICE_SENSITIVITY"), cls().device_sensitivity
            ),
        )


@dataclass
class MonitoringConfig:
    """Monitoring and metrics configuration."""

    # Feature toggles
    enable_monitoring: bool = True
    enable_metrics: bool = True
    enable_alerting: bool = True
    enable_structured_logging: bool = True

    # Metrics settings
    metrics_retention_hours: int = 24
    metrics_aggregation_interval_seconds: int = 60
    max_metrics_points: int = 10000

    # Alerting settings
    alert_cooldown_minutes: int = 5
    max_alerts_history: int = 1000
    enable_email_alerts: bool = False
    email_alert_recipients: List[str] = field(default_factory=list)

    # Performance monitoring
    enable_performance_tracking: bool = True
    slow_operation_threshold_ms: float = 1000.0
    track_user_activity: bool = True

    # Log settings
    log_level: str = "INFO"
    structured_log_format: str = "json"
    enable_request_logging: bool = True

    @classmethod
    def from_env(cls) -> "MonitoringConfig":
        """Create configuration from environment variables."""
        email_recipients = os.getenv("AUTH_ALERT_EMAIL_RECIPIENTS", "")
        recipients = (
            [r.strip() for r in email_recipients.split(",") if r.strip()]
            if email_recipients
            else []
        )

        return cls(
            enable_monitoring=_env_bool(
                os.getenv("AUTH_ENABLE_MONITORING"), cls().enable_monitoring
            ),
            enable_metrics=_env_bool(
                os.getenv("AUTH_ENABLE_METRICS"), cls().enable_metrics
            ),
            enable_alerting=_env_bool(
                os.getenv("AUTH_ENABLE_ALERTING"), cls().enable_alerting
            ),
            enable_structured_logging=_env_bool(
                os.getenv("AUTH_ENABLE_STRUCTURED_LOGGING"),
                cls().enable_structured_logging,
            ),
            metrics_retention_hours=_env_int(
                os.getenv("AUTH_METRICS_RETENTION_HOURS"), cls().metrics_retention_hours
            ),
            metrics_aggregation_interval_seconds=_env_int(
                os.getenv("AUTH_METRICS_AGGREGATION_INTERVAL"),
                cls().metrics_aggregation_interval_seconds,
            ),
            max_metrics_points=_env_int(
                os.getenv("AUTH_MAX_METRICS_POINTS"), cls().max_metrics_points
            ),
            alert_cooldown_minutes=_env_int(
                os.getenv("AUTH_ALERT_COOLDOWN_MINUTES"), cls().alert_cooldown_minutes
            ),
            max_alerts_history=_env_int(
                os.getenv("AUTH_MAX_ALERTS_HISTORY"), cls().max_alerts_history
            ),
            enable_email_alerts=_env_bool(
                os.getenv("AUTH_ENABLE_EMAIL_ALERTS"), cls().enable_email_alerts
            ),
            email_alert_recipients=recipients,
            enable_performance_tracking=_env_bool(
                os.getenv("AUTH_ENABLE_PERFORMANCE_TRACKING"),
                cls().enable_performance_tracking,
            ),
            slow_operation_threshold_ms=_env_float(
                os.getenv("AUTH_SLOW_OPERATION_THRESHOLD_MS"),
                cls().slow_operation_threshold_ms,
            ),
            track_user_activity=_env_bool(
                os.getenv("AUTH_TRACK_USER_ACTIVITY"), cls().track_user_activity
            ),
            log_level=os.getenv("AUTH_LOG_LEVEL", cls().log_level),
            structured_log_format=os.getenv(
                "AUTH_STRUCTURED_LOG_FORMAT", cls().structured_log_format
            ),
            enable_request_logging=_env_bool(
                os.getenv("AUTH_ENABLE_REQUEST_LOGGING"), cls().enable_request_logging
            ),
        )


@dataclass
class FeatureToggles:
    """Feature toggles for enabling/disabling authentication components."""

    # Core features
    use_database: bool = True
    enable_refresh_tokens: bool = True
    enable_password_reset: bool = True
    enable_email_verification: bool = True
    enable_two_factor_auth: bool = False

    # Security features
    enable_security_features: bool = True
    enable_rate_limiting: bool = True
    enable_audit_logging: bool = True
    enable_session_validation: bool = True

    # Intelligence features
    enable_intelligent_auth: bool = False
    enable_anomaly_detection: bool = False
    enable_behavioral_analysis: bool = False

    # Advanced features
    enable_multi_tenant: bool = True
    enable_role_based_access: bool = True
    enable_user_preferences: bool = True

    @classmethod
    def from_env(cls) -> "FeatureToggles":
        """Create configuration from environment variables."""
        # Legacy environment variable mappings for backward compatibility
        legacy_rate_limit = os.getenv("AUTH_ENABLE_RATE_LIMITER")
        legacy_intelligent = os.getenv("AUTH_ENABLE_INTELLIGENT_CHECKS")

        # Determine values with fallbacks to legacy variables when new ones are unset
        rate_limit_env = os.getenv("AUTH_ENABLE_RATE_LIMITING", legacy_rate_limit)
        intelligent_auth_env = os.getenv(
            "AUTH_ENABLE_INTELLIGENT_AUTH", legacy_intelligent
        )

        anomaly_env = os.getenv("AUTH_ENABLE_ANOMALY_DETECTION")
        behavioral_env = os.getenv("AUTH_ENABLE_BEHAVIORAL_ANALYSIS")

        if legacy_intelligent is not None:
            anomaly_env = anomaly_env or legacy_intelligent
            behavioral_env = behavioral_env or legacy_intelligent

        return cls(
            use_database=_env_bool(os.getenv("AUTH_USE_DATABASE"), cls().use_database),
            enable_refresh_tokens=_env_bool(
                os.getenv("AUTH_ENABLE_REFRESH_TOKENS"), cls().enable_refresh_tokens
            ),
            enable_password_reset=_env_bool(
                os.getenv("AUTH_ENABLE_PASSWORD_RESET"), cls().enable_password_reset
            ),
            enable_email_verification=_env_bool(
                os.getenv("AUTH_ENABLE_EMAIL_VERIFICATION"),
                cls().enable_email_verification,
            ),
            enable_two_factor_auth=_env_bool(
                os.getenv("AUTH_ENABLE_TWO_FACTOR_AUTH"), cls().enable_two_factor_auth
            ),
            enable_security_features=_env_bool(
                os.getenv("AUTH_ENABLE_SECURITY_FEATURES"),
                cls().enable_security_features,
            ),
            enable_rate_limiting=_env_bool(rate_limit_env, cls().enable_rate_limiting),
            enable_audit_logging=_env_bool(
                os.getenv("AUTH_ENABLE_AUDIT_LOGGING"), cls().enable_audit_logging
            ),
            enable_session_validation=_env_bool(
                os.getenv("AUTH_ENABLE_SESSION_VALIDATION"),
                cls().enable_session_validation,
            ),
            enable_intelligent_auth=_env_bool(
                intelligent_auth_env, cls().enable_intelligent_auth
            ),
            enable_anomaly_detection=_env_bool(
                anomaly_env, cls().enable_anomaly_detection
            ),
            enable_behavioral_analysis=_env_bool(
                behavioral_env, cls().enable_behavioral_analysis
            ),
            enable_multi_tenant=_env_bool(
                os.getenv("AUTH_ENABLE_MULTI_TENANT"), cls().enable_multi_tenant
            ),
            enable_role_based_access=_env_bool(
                os.getenv("AUTH_ENABLE_ROLE_BASED_ACCESS"),
                cls().enable_role_based_access,
            ),
            enable_user_preferences=_env_bool(
                os.getenv("AUTH_ENABLE_USER_PREFERENCES"), cls().enable_user_preferences
            ),
        )


@dataclass
class AuthConfig:
    """
    Comprehensive authentication configuration for the consolidated service.

    This replaces all the fragmented configuration classes across different
    auth services with a single, unified configuration system.
    """

    # Core configuration sections
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    jwt: JWTConfig = field(default_factory=JWTConfig)
    session: SessionConfig = field(default_factory=SessionConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    intelligence: IntelligenceConfig = field(default_factory=IntelligenceConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    features: FeatureToggles = field(default_factory=FeatureToggles)

    # Service metadata
    service_name: str = "consolidated-auth-service"
    service_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = False

    @classmethod
    def from_env(cls) -> "AuthConfig":
        """Create configuration from environment variables."""
        return cls(
            database=DatabaseConfig.from_env(),
            jwt=JWTConfig.from_env(),
            session=SessionConfig.from_env(),
            security=SecurityConfig.from_env(),
            intelligence=IntelligenceConfig.from_env(),
            monitoring=MonitoringConfig.from_env(),
            features=FeatureToggles.from_env(),
            service_name=os.getenv("AUTH_SERVICE_NAME", cls().service_name),
            service_version=os.getenv("AUTH_SERVICE_VERSION", cls().service_version),
            environment=os.getenv("AUTH_ENVIRONMENT", cls().environment),
            debug=_env_bool(os.getenv("AUTH_DEBUG"), cls().debug),
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuthConfig":
        """Create configuration from a dictionary."""
        return cls(
            database=DatabaseConfig(**data.get("database", {})),
            jwt=JWTConfig(**data.get("jwt", {})),
            session=SessionConfig(**data.get("session", {})),
            security=SecurityConfig(**data.get("security", {})),
            intelligence=IntelligenceConfig(**data.get("intelligence", {})),
            monitoring=MonitoringConfig(**data.get("monitoring", {})),
            features=FeatureToggles(**data.get("features", {})),
            service_name=data.get("service_name", cls().service_name),
            service_version=data.get("service_version", cls().service_version),
            environment=data.get("environment", cls().environment),
            debug=data.get("debug", cls().debug),
        )

    @classmethod
    def from_file(
        cls, file_path: Union[str, Path], env: Optional[str] = None
    ) -> "AuthConfig":
        """
        Load configuration for a specific environment from a JSON or YAML file.

        The configuration file may either contain a single configuration mapping
        or be structured by environment name at the top level. When ``env`` is
        provided, the corresponding section will be loaded. If the section is
        missing a ``ValueError`` is raised.
        """

        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")

        suffix = path.suffix.lower()
        if suffix == ".json":
            data = json.loads(path.read_text() or "{}")
        elif suffix in {".yaml", ".yml"}:
            if yaml is None:
                raise ValueError("PyYAML is required to load YAML configuration")
            data = yaml.safe_load(path.read_text()) or {}
        else:
            raise ValueError(f"Unsupported configuration format: {suffix}")

        if env is not None:
            try:
                env_data = data[env]
            except (KeyError, TypeError):
                raise ValueError(
                    f"Environment '{env}' not found in configuration file"
                )
        else:
            env_data = data

        if env is not None:
            missing: List[str] = []
            if not env_data.get("database", {}).get("database_url"):
                missing.append("database.database_url")
            if env in ("production", "prod") and not env_data.get("jwt", {}).get(
                "secret_key"
            ):
                missing.append("jwt.secret_key")
            if missing:
                raise ValueError(
                    f"Missing mandatory fields for environment '{env}': "
                    + ", ".join(missing)
                )

        config = cls.from_dict(env_data)
        config.environment = env or config.environment
        config.validate()
        return config

    @classmethod
    def from_environment(
        cls, env: str, config_dir: Union[str, Path] = "config"
    ) -> "AuthConfig":
        """Load configuration for ``env`` from default config directory."""

        config_dir_path = Path(config_dir)
        candidates = [
            config_dir_path / "auth_config.yaml",
            config_dir_path / "auth_config.yml",
            config_dir_path / "auth_config.json",
        ]
        path = next((p for p in candidates if p.exists()), None)
        if path is None:
            raise FileNotFoundError(
                f"No configuration file found in {config_dir_path}"
            )
        return cls.from_file(path, env)

    @classmethod
    def from_env_file(cls, file_path: Union[str, Path]) -> "AuthConfig":
        """Load configuration from a .env file."""
        _load_env_file(file_path)
        return cls.from_env()

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "database": {
                "database_url": self.database.database_url,
                "connection_pool_size": self.database.connection_pool_size,
                "connection_pool_max_overflow": self.database.connection_pool_max_overflow,
                "connection_timeout_seconds": self.database.connection_timeout_seconds,
                "query_timeout_seconds": self.database.query_timeout_seconds,
                "enable_query_logging": self.database.enable_query_logging,
            },
            "jwt": {
                "secret_key": self.jwt.secret_key,
                "algorithm": self.jwt.algorithm,
                "access_token_expire_minutes": self.jwt.access_token_expire_minutes,
                "refresh_token_expire_days": self.jwt.refresh_token_expire_days,
                "password_reset_token_expire_hours": self.jwt.password_reset_token_expire_hours,
                "email_verification_token_expire_hours": self.jwt.email_verification_token_expire_hours,
            },
            "session": {
                "session_timeout_hours": self.session.session_timeout_hours,
                "max_sessions_per_user": self.session.max_sessions_per_user,
                "storage_type": self.session.storage_type,
                "redis_url": self.session.redis_url,
                "cookie_name": self.session.cookie_name,
                "cookie_secure": self.session.cookie_secure,
                "cookie_httponly": self.session.cookie_httponly,
                "cookie_samesite": self.session.cookie_samesite,
            },
            "security": {
                "enable_rate_limiting": self.security.enable_rate_limiting,
                "max_failed_attempts": self.security.max_failed_attempts,
                "lockout_duration_minutes": self.security.lockout_duration_minutes,
                "rate_limit_window_minutes": self.security.rate_limit_window_minutes,
                "rate_limit_max_requests": self.security.rate_limit_max_requests,
                "min_password_length": self.security.min_password_length,
                "require_password_complexity": self.security.require_password_complexity,
                "password_hash_rounds": self.security.password_hash_rounds,
                "password_hash_algorithm": self.security.password_hash_algorithm,
                "enable_session_validation": self.security.enable_session_validation,
                "validate_ip_address": self.security.validate_ip_address,
                "validate_user_agent": self.security.validate_user_agent,
                "enable_device_fingerprinting": self.security.enable_device_fingerprinting,
                "enable_audit_logging": self.security.enable_audit_logging,
                "log_successful_logins": self.security.log_successful_logins,
                "log_failed_logins": self.security.log_failed_logins,
                "log_security_events": self.security.log_security_events,
            },
            "intelligence": {
                "enable_intelligent_auth": self.intelligence.enable_intelligent_auth,
                "enable_anomaly_detection": self.intelligence.enable_anomaly_detection,
                "enable_behavioral_analysis": self.intelligence.enable_behavioral_analysis,
                "enable_threat_detection": self.intelligence.enable_threat_detection,
                "risk_threshold_low": self.intelligence.risk_threshold_low,
                "risk_threshold_medium": self.intelligence.risk_threshold_medium,
                "risk_threshold_high": self.intelligence.risk_threshold_high,
                "model_update_interval_hours": self.intelligence.model_update_interval_hours,
                "min_training_samples": self.intelligence.min_training_samples,
                "enable_online_learning": self.intelligence.enable_online_learning,
                "behavioral_window_days": self.intelligence.behavioral_window_days,
                "location_sensitivity": self.intelligence.location_sensitivity,
                "time_sensitivity": self.intelligence.time_sensitivity,
                "device_sensitivity": self.intelligence.device_sensitivity,
            },
            "monitoring": {
                "enable_monitoring": self.monitoring.enable_monitoring,
                "enable_metrics": self.monitoring.enable_metrics,
                "enable_alerting": self.monitoring.enable_alerting,
                "enable_structured_logging": self.monitoring.enable_structured_logging,
                "metrics_retention_hours": self.monitoring.metrics_retention_hours,
                "metrics_aggregation_interval_seconds": self.monitoring.metrics_aggregation_interval_seconds,
                "max_metrics_points": self.monitoring.max_metrics_points,
                "alert_cooldown_minutes": self.monitoring.alert_cooldown_minutes,
                "max_alerts_history": self.monitoring.max_alerts_history,
                "enable_email_alerts": self.monitoring.enable_email_alerts,
                "email_alert_recipients": self.monitoring.email_alert_recipients,
                "enable_performance_tracking": self.monitoring.enable_performance_tracking,
                "slow_operation_threshold_ms": self.monitoring.slow_operation_threshold_ms,
                "track_user_activity": self.monitoring.track_user_activity,
                "log_level": self.monitoring.log_level,
                "structured_log_format": self.monitoring.structured_log_format,
                "enable_request_logging": self.monitoring.enable_request_logging,
            },
            "features": {
                "use_database": self.features.use_database,
                "enable_refresh_tokens": self.features.enable_refresh_tokens,
                "enable_password_reset": self.features.enable_password_reset,
                "enable_email_verification": self.features.enable_email_verification,
                "enable_two_factor_auth": self.features.enable_two_factor_auth,
                "enable_security_features": self.features.enable_security_features,
                "enable_rate_limiting": self.features.enable_rate_limiting,
                "enable_audit_logging": self.features.enable_audit_logging,
                "enable_session_validation": self.features.enable_session_validation,
                "enable_intelligent_auth": self.features.enable_intelligent_auth,
                "enable_anomaly_detection": self.features.enable_anomaly_detection,
                "enable_behavioral_analysis": self.features.enable_behavioral_analysis,
                "enable_multi_tenant": self.features.enable_multi_tenant,
                "enable_role_based_access": self.features.enable_role_based_access,
                "enable_user_preferences": self.features.enable_user_preferences,
            },
            "service_name": self.service_name,
            "service_version": self.service_version,
            "environment": self.environment,
            "debug": self.debug,
        }

    def validate(self) -> None:
        """Validate configuration and raise errors for invalid settings."""
        errors = []

        # JWT validation
        if not self.jwt.secret_key or self.jwt.secret_key == "change-me-in-production":
            if self.environment in ("production", "prod"):
                errors.append("JWT secret key must be set in production")

        if self.jwt.access_token_expire_minutes <= 0:
            errors.append("Access token expiry must be positive")

        if self.jwt.refresh_token_expire_days <= 0:
            errors.append("Refresh token expiry must be positive")

        # Session validation
        if self.session.storage_type == "redis" and not self.session.redis_url:
            errors.append("Redis URL required when session storage type is 'redis'")

        if self.session.session_timeout_hours <= 0:
            errors.append("Session timeout must be positive")

        if self.session.max_sessions_per_user <= 0:
            errors.append("Max sessions per user must be positive")

        # Security validation
        if self.security.max_failed_attempts <= 0:
            errors.append("Max failed attempts must be positive")

        if self.security.lockout_duration_minutes <= 0:
            errors.append("Lockout duration must be positive")

        if self.security.min_password_length < 4:
            errors.append("Minimum password length must be at least 4")

        if self.security.password_hash_algorithm == "bcrypt":
            if not (4 <= self.security.password_hash_rounds <= 20):
                errors.append("Password hash rounds must be between 4 and 20")
        elif self.security.password_hash_algorithm != "argon2":
            errors.append("Unsupported password hash algorithm")

        # Intelligence validation
        if not (0.0 <= self.intelligence.risk_threshold_low <= 1.0):
            errors.append("Risk threshold low must be between 0.0 and 1.0")

        if not (0.0 <= self.intelligence.risk_threshold_medium <= 1.0):
            errors.append("Risk threshold medium must be between 0.0 and 1.0")

        if not (0.0 <= self.intelligence.risk_threshold_high <= 1.0):
            errors.append("Risk threshold high must be between 0.0 and 1.0")

        if (
            self.intelligence.risk_threshold_low
            >= self.intelligence.risk_threshold_medium
        ):
            errors.append("Risk threshold low must be less than medium")

        if (
            self.intelligence.risk_threshold_medium
            >= self.intelligence.risk_threshold_high
        ):
            errors.append("Risk threshold medium must be less than high")

        # Database validation
        if self.features.use_database and not self.database.database_url:
            errors.append("Database URL required when use_database is enabled")

        if errors:
            raise ValueError(
                "Invalid authentication configuration:\n"
                + "\n".join(f"- {error}" for error in errors)
            )

    def get_mode_description(self) -> str:
        """Get a description of the current authentication mode."""
        modes = []

        if self.features.use_database:
            modes.append("database-backed")
        else:
            modes.append("in-memory")

        if self.features.enable_security_features:
            modes.append("security-enhanced")

        if self.features.enable_intelligent_auth:
            modes.append("intelligent")

        if self.features.enable_two_factor_auth:
            modes.append("2FA-enabled")

        return f"Consolidated auth service ({', '.join(modes)})"

    @classmethod
    def load(
        cls,
        file_path: Optional[Union[str, Path]] = None,
        env: Optional[str] = None,
    ) -> "AuthConfig":
        """
        Load configuration from various sources with automatic detection.

        Priority order:
        1. Explicit file_path if provided
        2. Environment-specific files (.env.{env}, auth_config.{env}.json, etc.)
        3. Default files (.env, auth_config.json, etc.)
        4. Environment variables only
        """
        path: Optional[Path] = None

        if file_path:
            path = Path(file_path)
        else:
            env = (
                env or os.getenv("AUTH_ENV") or os.getenv("APP_ENV") or os.getenv("ENV")
            )
            candidates = []

            if env:
                candidates.extend(
                    [
                        Path(f".env.{env}"),
                        Path(f"auth_config.{env}.json"),
                        Path(f"auth_config.{env}.yaml"),
                        Path(f"auth_config.{env}.yml"),
                    ]
                )

            candidates.extend(
                [
                    Path(".env"),
                    Path("auth_config.json"),
                    Path("auth_config.yaml"),
                    Path("auth_config.yml"),
                ]
            )

            path = next((p for p in candidates if p.exists()), None)

        if path and path.exists():
            if path.name.lower() == ".env" or path.suffix.lower() == ".env":
                config = cls.from_env_file(path)
            else:
                config = cls.from_file(path, env)
        else:
            config = cls.from_env()

        config.validate()
        return config
