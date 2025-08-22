"""
Base classes with common functionality for reportHanter.
"""
from typing import Any, Dict, Optional, Union
from pathlib import Path
import pandas as pd
import altair as alt
import logging
from .interfaces import DataProcessor, PlotGenerator
from .exceptions import FileValidationError, DataProcessingError, PlotGenerationError


class BaseDataProcessor(DataProcessor):
    """Base implementation for data processors with common functionality."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def validate_input(self, file_path: Union[str, Path]) -> bool:
        """Validate that the input file exists and is readable."""
        path = Path(file_path)
        if not path.exists():
            raise FileValidationError(f"File does not exist: {file_path}")
        if not path.is_file():
            raise FileValidationError(f"Path is not a file: {file_path}")
        if not path.stat().st_size > 0:
            raise FileValidationError(f"File is empty: {file_path}")
        return True
    
    def process(self, file_path: Union[str, Path]) -> pd.DataFrame:
        """Process the input file with error handling."""
        self.validate_input(file_path)
        try:
            self.logger.info(f"Processing file: {file_path}")
            result = self._process_file(file_path)
            self.logger.info(f"Successfully processed {len(result)} records")
            return result
        except Exception as e:
            self.logger.error(f"Failed to process file {file_path}: {e}")
            raise DataProcessingError(f"Failed to process {file_path}: {e}")
    
    def _process_file(self, file_path: Union[str, Path]) -> pd.DataFrame:
        """Override this method in subclasses."""
        raise NotImplementedError("Subclasses must implement _process_file")


class BasePlotGenerator(PlotGenerator):
    """Base implementation for plot generators with common styling."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def generate_plot(self, data: pd.DataFrame, **kwargs) -> alt.Chart:
        """Generate plot with error handling and common styling."""
        try:
            if data.empty:
                return self._empty_chart(**kwargs)
            
            chart = self._create_chart(data, **kwargs)
            return self._apply_styling(chart)
            
        except Exception as e:
            self.logger.error(f"Failed to generate plot: {e}")
            raise PlotGenerationError(f"Failed to generate plot: {e}")
    
    def _create_chart(self, data: pd.DataFrame, **kwargs) -> alt.Chart:
        """Override this method in subclasses."""
        raise NotImplementedError("Subclasses must implement _create_chart")
    
    def _empty_chart(self, title: str = "No Data Available", **kwargs) -> alt.Chart:
        """Create a placeholder chart for empty data."""
        return alt.Chart(pd.DataFrame({"message": [title]})).mark_text(
            fontSize=20, color="gray"
        ).encode(
            text="message:N"
        ).properties(
            title=title,
            width=self.config.get("width", "container"),
            height=self.config.get("height", 200)
        )
    
    def _apply_styling(self, chart: alt.Chart) -> alt.Chart:
        """Apply common styling to charts."""
        return chart.properties(
            width=self.config.get("width", "container"),
            height=self.config.get("height", 400)
        ).resolve_scale(
            color="independent"
        )