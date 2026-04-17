"""
Configuration module for Insurance Policy Analyzer.

Centralizes all configuration values with validation.
"""

import os
from pathlib import Path
from typing import Optional

# Load .env file if present (project root)
def _load_env():
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    root = Path(__file__).resolve().parent
    for path in (root / ".env", Path.cwd() / ".env"):
        if path.exists():
            load_dotenv(path, override=True)
            break


_load_env()


def _env_str(key: str, default: str = "") -> str:
    """Get string env var, stripped."""
    return os.getenv(key, default).strip()


def _env_int(key: str, default: int) -> int:
    """Get int env var with fallback."""
    try:
        return int(os.getenv(key, str(default)))
    except (ValueError, TypeError):
        return default


def _env_float(key: str, default: float) -> float:
    """Get float env var with fallback."""
    try:
        return float(os.getenv(key, str(default)))
    except (ValueError, TypeError):
        return default


def _env_bool(key: str, default: bool = False) -> bool:
    """Get bool env var."""
    val = os.getenv(key, "").lower().strip()
    if val in ("1", "true", "yes", "on"):
        return True
    if val in ("0", "false", "no", "off"):
        return False
    return default


# Gemini API Configuration
GEMINI_API_KEY: str = _env_str("GEMINI_API_KEY")
GEMINI_MODEL: str = _env_str("GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_MAX_TOKENS: int = _env_int("GEMINI_MAX_TOKENS", 4096)
GEMINI_TIMEOUT: int = _env_int("GEMINI_TIMEOUT", 90)

# Flask API Configuration
FLASK_HOST: str = _env_str("FLASK_HOST", "127.0.0.1")
FLASK_PORT: int = _env_int("FLASK_PORT", 5000)
FLASK_DEBUG: bool = _env_bool("FLASK_DEBUG", False)
API_MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024  # 16 MB

# PDF Processing
PDF_MAX_WORDS: int = 15_000
PDF_CHUNK_SIZE: int = 10_000
PDF_MAX_CHARS_PER_CHUNK: int = 12_000

# Financial Defaults
DEFAULT_INFLATION_RATE: float = 0.06
FD_RETURN_RATE: float = 0.07
MF_SIP_RETURN_RATE: float = 0.12

# Risk Analyzer Keywords
RISKY_KEYWORDS: tuple[str, ...] = (
    "not covered",
    "subject to",
    "conditions apply",
    "waiting period",
    "excluded",
    "limited to",
    "at discretion",
    "may vary",
)

ALLOWED_EXTENSIONS: set[str] = {"pdf"}


def validate_config() -> Optional[str]:
    """
    Validate required configuration.

    Returns:
        Error message if invalid, None if valid.
    """
    if not GEMINI_API_KEY:
        return "GEMINI_API_KEY environment variable is not set. Add it to .env or set in environment."
    if GEMINI_MAX_TOKENS < 256 or GEMINI_MAX_TOKENS > 8192:
        return "GEMINI_MAX_TOKENS must be between 256 and 8192"
    if FLASK_PORT < 1 or FLASK_PORT > 65535:
        return "FLASK_PORT must be between 1 and 65535"
    return None
