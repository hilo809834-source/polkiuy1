"""
Core configuration settings.
All secrets and model configs are driven by environment variables or config files.
Nothing hardcoded.
"""
import os
from typing import Dict, Optional

# Model configuration - driven by environment variables, never hardcoded
MODEL_CONFIG: Dict[str, Dict[str, str]] = {
    "fast": {
        "provider": os.getenv("MODEL_FAST_PROVIDER", "openai"),
        "model": os.getenv("MODEL_FAST_MODEL", "gpt-4o-mini"),
    },
    "mid": {
        "provider": os.getenv("MODEL_MID_PROVIDER", "openai"),
        "model": os.getenv("MODEL_MID_MODEL", "gpt-4o"),
    },
    "frontier": {
        "provider": os.getenv("MODEL_FRONTIER_PROVIDER", "anthropic"),
        "model": os.getenv("MODEL_FRONTIER_MODEL", "claude-sonnet-4-20250514"),
    },
}

# API keys - loaded from environment, never hardcoded
API_KEYS: Dict[str, Optional[str]] = {
    "openai": os.getenv("OPENAI_API_KEY"),
    "anthropic": os.getenv("ANTHROPIC_API_KEY"),
    "huggingface": os.getenv("HUGGINGFACE_API_KEY"),
}

# Retry configuration
MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
RETRY_DELAY_SECONDS: float = float(os.getenv("RETRY_DELAY_SECONDS", "1.0"))

# Sandbox configuration
DOCKER_TIMEOUT_SECONDS: int = int(os.getenv("DOCKER_TIMEOUT_SECONDS", "300"))
DOCKER_MEMORY_LIMIT: str = os.getenv("DOCKER_MEMORY_LIMIT", "512m")
DOCKER_CPU_LIMIT: float = float(os.getenv("DOCKER_CPU_LIMIT", "1.0"))

# Secrets detection patterns
SECRETS_PATTERNS = [
    r'(?i)(api[_-]?key|secret[_-]?key|access[_-]?token|auth[_-]?token|bearer)\s*[=:]\s*["\']?[\w-]{20,}["\']?',
    r'(?i)(password|passwd|pwd)\s*[=:]\s*["\']?[^\s"\']{8,}["\']?',
    r'-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----',
    r'ghp_[a-zA-Z0-9]{36}',
    r'gho_[a-zA-Z0-9]{36}',
]

# Log redaction - patterns to redact before logging
LOG_REDACTION_PATTERNS = [
    (r'(api[_-]?key["\s:=]+)[^"\'\s,}]+', r'\1***REDACTED***'),
    (r'(bearer["\s:=]+)[^"\'\s,}]+', r'\1***REDACTED***'),
    (r'(token["\s:=]+)[^"\'\s,}]+', r'\1***REDACTED***'),
]
