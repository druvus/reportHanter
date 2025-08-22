"""
Flagstat data processor with improved error handling and configuration.
"""
from typing import Any, Dict, Union, Tuple
from pathlib import Path
import re
import pandas as pd
import altair as alt
import panel as pn
import logging

from ..core.base import BaseDataProcessor, BasePlotGenerator
from ..core.exceptions import DataProcessingError


class FlagstatProcessor(BaseDataProcessor):
    """Processes BWA flagstat files into alignment statistics."""
    
    def validate_input(self, file_path: Union[str, Path]) -> bool:
        """Validate flagstat file format."""
        super().validate_input(file_path)
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Check for expected patterns
            if "paired in sequencing" not in content:
                raise DataProcessingError("File doesn't appear to be a BWA flagstat output")
                
        except Exception as e:
            raise DataProcessingError(f"Invalid flagstat file: {e}")
        
        return True
    
    def _process_file(self, file_path: Union[str, Path]) -> pd.DataFrame:
        """Process flagstat file into DataFrame with alignment statistics."""
        total_reads, percent_mapped = self._parse_flagstat(file_path)
        
        # Create a simple DataFrame with the statistics
        return pd.DataFrame({
            "metric": ["total_reads", "percent_mapped", "reads_mapped", "reads_unmapped"],
            "value": [
                total_reads,
                percent_mapped,
                int(total_reads * percent_mapped / 100),
                int(total_reads * (100 - percent_mapped) / 100)
            ]
        })
    
    def _parse_flagstat(self, file_path: Union[str, Path]) -> Tuple[int, float]:
        """Parse BWA flagstat file to extract reads and mapping percentage."""
        pattern_total = r"(\d+) \+ \d+ paired in sequencing"
        pattern_mapped = r"(\d+) \+ \d+ with itself and mate mapped"
        
        with open(file_path, 'r') as f:
            content = f.read()
        
        try:
            total_matches = re.findall(pattern_total, content)
            mapped_matches = re.findall(pattern_mapped, content)
            
            if not total_matches:
                raise DataProcessingError("Could not find 'paired in sequencing' in flagstat file")
            if not mapped_matches:
                raise DataProcessingError("Could not find 'with itself and mate mapped' in flagstat file")
            
            total_reads = int(total_matches[0])
            total_mapped = int(mapped_matches[0])
            
            if total_reads == 0:
                percent_mapped = 0.0
            else:
                percent_mapped = (total_mapped / total_reads) * 100
                
            return total_reads, percent_mapped
            
        except (ValueError, IndexError) as e:
            raise DataProcessingError(f"Error parsing flagstat file: {e}")
    
    def create_alignment_stats(self, 
                             data: pd.DataFrame, 
                             species: str = "Host") -> Tuple[pn.pane.Markdown, pn.pane.Vega]:
        """Create alignment statistics markdown and chart."""
        stats_dict = dict(zip(data['metric'], data['value']))
        
        total_reads = stats_dict.get('total_reads', 0)
        percent_mapped = stats_dict.get('percent_mapped', 0.0)
        reads_mapped = stats_dict.get('reads_mapped', 0)
        reads_unmapped = stats_dict.get('reads_unmapped', 0)
        
        # Create markdown summary
        stats_md = pn.pane.Markdown(
            f"""
            ### Total Number of Reads: 
            {total_reads:,}
            ### Reads aligned to {species} Genome: 
            {reads_mapped:,} ({percent_mapped:.2f}%)
            ### Reads NOT aligned to {species} Genome:
            {reads_unmapped:,} ({100 - percent_mapped:.2f}%)
            """,
            name=f"{species} Alignment Stats"
        )
        
        # Create chart
        plot_generator = FlagstatPlotGenerator()
        chart = plot_generator.generate_plot(
            data, 
            species=species, 
            title=f"Reads aligned to {species}"
        ).interactive()
        
        chart_pane = pn.pane.Vega(
            chart, 
            sizing_mode="stretch_both", 
            name=f"{species} Alignment Plot"
        )
        
        return stats_md, chart_pane


class FlagstatPlotGenerator(BasePlotGenerator):
    """Generates Altair charts for alignment statistics."""
    
    def _create_chart(self, data: pd.DataFrame, **kwargs) -> alt.Chart:
        """Create alignment statistics normalized bar chart."""
        species = kwargs.get("species", "Host")
        title = kwargs.get("title", f"Reads aligned to {species}")
        
        # Extract the data we need
        stats_dict = dict(zip(data['metric'], data['value']))
        reads_mapped = stats_dict.get('reads_mapped', 0)
        reads_unmapped = stats_dict.get('reads_unmapped', 0)
        
        # Create visualization DataFrame
        viz_data = pd.DataFrame({
            "amount": [reads_unmapped, reads_mapped],
            "type": ["unaligned", "aligned"]
        })
        
        chart = (
            alt.Chart(viz_data, title=title)
            .mark_bar()
            .encode(
                x=alt.X(
                    "sum(amount)", 
                    stack="normalize", 
                    axis=alt.Axis(format="%"), 
                    title=None
                ),
                color=alt.Color(
                    "type:N", 
                    scale=alt.Scale(scheme='dark2'),
                    title=None
                ),
                tooltip=[
                    alt.Tooltip("amount:Q", title="Number of reads"),
                    alt.Tooltip("type:N", title="Type")
                ],
            )
            .properties(height=100)
        )
        
        return chart