"""
Kraken data processor with improved error handling and configuration.
"""
from typing import Any, Dict, Optional, Union, Tuple
from pathlib import Path
import pandas as pd
import numpy as np
import altair as alt
import logging

from ..core.base import BaseDataProcessor, BasePlotGenerator
from ..core.exceptions import DataProcessingError


class KrakenProcessor(BaseDataProcessor):
    """Processes Kraken TSV files into standardized DataFrames."""
    
    TAXONOMY_LEVELS = {
        "domain": "D",
        "phylum": "P",
        "class": "K",
        "order": "O",
        "family": "F",
        "genus": "G",
        "species": "S",
    }
    
    def validate_input(self, file_path: Union[str, Path]) -> bool:
        """Validate Kraken file format."""
        super().validate_input(file_path)
        
        # Check if it looks like a Kraken file
        try:
            test_df = pd.read_csv(file_path, sep="\t", nrows=5, header=None)
            if test_df.shape[1] != 6:
                raise DataProcessingError(f"Expected 6 columns in Kraken file, got {test_df.shape[1]}")
        except Exception as e:
            raise DataProcessingError(f"Invalid Kraken file format: {e}")
        
        return True
    
    def _process_file(self, file_path: Union[str, Path]) -> pd.DataFrame:
        """Process Kraken TSV file into DataFrame."""
        df = pd.read_csv(
            file_path,
            sep="\t",
            header=None,
            names=["percent", "count_clades", "count", "tax_lvl", "taxonomy_id", "name"]
        )
        
        return (
            df.assign(name=lambda x: x.name.str.strip())
            .assign(
                domain=lambda x: np.select(
                    [x.tax_lvl.isin(["D", "U", "R"])],
                    [x.name],
                    default=pd.NA
                )
            )
            .ffill()
            .assign(percent=lambda x: x.percent / 100)
        )
    
    def filter_data(self, 
                   data: pd.DataFrame, 
                   level: str = "species", 
                   cutoff: float = 0.01,
                   max_entries: int = 10, 
                   virus_only: bool = True) -> Tuple[pd.DataFrame, float]:
        """Filter Kraken data by taxonomy level and other criteria."""
        
        if level not in self.TAXONOMY_LEVELS:
            raise ValueError(f"Invalid taxonomy level: {level}. Must be one of {list(self.TAXONOMY_LEVELS.keys())}")
        
        # Get unclassified percentage
        unclassified_rows = data.loc[data.domain == "unclassified"]
        unclassified_pct = unclassified_rows.percent.iloc[0] if len(unclassified_rows) > 0 else 0.0
        
        # Filter by taxonomy level and cutoff
        filtered_df = (
            data.loc[data.tax_lvl == self.TAXONOMY_LEVELS[level]]
            .loc[data.percent > cutoff]
            .sort_values("percent", ascending=False)
        )
        
        # Apply virus filter if requested
        if virus_only:
            filtered_df = filtered_df.loc[filtered_df.domain == "Viruses"]
        
        return filtered_df.head(max_entries), unclassified_pct


class KrakenPlotGenerator(BasePlotGenerator):
    """Generates Altair charts for Kraken classification data."""
    
    def _create_chart(self, data: pd.DataFrame, **kwargs) -> alt.Chart:
        """Create Kraken classification bar chart."""
        title = kwargs.get("title", "Kraken classification")
        unclassified_pct = kwargs.get("unclassified_pct", 0.0)
        
        chart = (
            alt.Chart(data, title=title)
            .mark_bar()
            .encode(
                alt.X(
                    "percent:Q",
                    axis=alt.Axis(format="%"),
                    title=f"Percent of reads ({unclassified_pct * 100:.1f}% not classified)"
                ),
                alt.Y("name:N", sort="-x", title=None),
                alt.Color("name:N", title=None, legend=None),
                tooltip=[
                    alt.Tooltip("domain:N"),
                    alt.Tooltip("name:N", title="Species"),
                    alt.Tooltip("count_clades:Q", title="Number of reads"),
                    alt.Tooltip("percent:Q", title="Percentage", format=".2%")
                ],
            )
        )
        
        return chart