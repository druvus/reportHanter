"""
Custom exceptions for reportHanter.
"""


class ReportHanterError(Exception):
    """Base exception for all reportHanter errors."""
    pass


class DataProcessingError(ReportHanterError):
    """Raised when data processing fails."""
    pass


class FileValidationError(ReportHanterError):
    """Raised when file validation fails."""
    pass


class PlotGenerationError(ReportHanterError):
    """Raised when plot generation fails."""
    pass


class ConfigurationError(ReportHanterError):
    """Raised when configuration is invalid or missing."""
    pass


class ReportGenerationError(ReportHanterError):
    """Raised when report generation fails."""
    pass