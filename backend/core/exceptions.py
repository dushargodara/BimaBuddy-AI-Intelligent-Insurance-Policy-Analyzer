"""
Custom exceptions for Insurance Policy Analyzer.

Provides a clear exception hierarchy for production error handling.
"""


class PolicyAnalyzerError(Exception):
    """Base exception for policy analyzer."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ConfigurationError(PolicyAnalyzerError):
    """Raised when configuration is invalid or missing."""


class ValidationError(PolicyAnalyzerError):
    """Raised when input validation fails."""


class PDFProcessingError(PolicyAnalyzerError):
    """Raised when PDF extraction or processing fails."""


class AIAnalysisError(PolicyAnalyzerError):
    """Raised when AI/LLM analysis fails."""


class FinancialCalculationError(PolicyAnalyzerError):
    """Raised when financial calculation fails."""
