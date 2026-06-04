"""
Core interfaces and abstract base classes for reportHanter.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import altair as alt
import pandas as pd


class DataProcessor(ABC):
    """Abstract base class for all data processing modules."""

    @abstractmethod
    def process(self, file_path: str | Path) -> pd.DataFrame:
        """Process the input file and return a standardized DataFrame."""
        pass

    @abstractmethod
    def validate_input(self, file_path: str | Path) -> bool:
        """Validate that the input file exists and has the expected format."""
        pass


class PlotGenerator(ABC):
    """Abstract base class for all plotting modules."""

    @abstractmethod
    def generate_plot(self, data: pd.DataFrame, **kwargs: Any) -> alt.Chart:
        """Generate an Altair chart from processed data."""
        pass


class ReportSection(ABC):
    """Abstract base class for report sections."""

    @abstractmethod
    def generate_section(self, **kwargs: Any) -> Any:
        """Generate a Panel component for this report section."""
        pass

    @property
    @abstractmethod
    def section_name(self) -> str:
        """Return the name of this report section."""
        pass


class ConfigProvider(ABC):
    """Abstract base class for configuration providers."""

    @abstractmethod
    def get_config(self, section: str | None = None) -> dict[str, Any]:
        """Get configuration dictionary."""
        pass

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """Get a specific configuration value."""
        pass
