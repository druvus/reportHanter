"""
FastP data processor with improved error handling and configuration.
"""
from typing import Any, Dict, Union
from pathlib import Path
import json
import pandas as pd
import panel as pn
import logging

from ..core.base import BaseDataProcessor
from ..core.exceptions import DataProcessingError


class FastpProcessor(BaseDataProcessor):
    """Processes FastP JSON files into summary statistics."""
    
    def validate_input(self, file_path: Union[str, Path]) -> bool:
        """Validate FastP JSON file format."""
        super().validate_input(file_path)
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Check for required sections
            if 'summary' not in data:
                raise DataProcessingError("Missing 'summary' section in FastP JSON")
                
        except json.JSONDecodeError as e:
            raise DataProcessingError(f"Invalid JSON format: {e}")
        except Exception as e:
            raise DataProcessingError(f"Error validating FastP JSON: {e}")
        
        return True
    
    def _process_file(self, file_path: Union[str, Path]) -> pd.DataFrame:
        """Process FastP JSON file into summary statistics."""
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        stats = self._extract_statistics(data)
        
        # Convert to DataFrame for consistency with other processors
        return pd.DataFrame(list(stats.items()), columns=["Metric", "Value"])
    
    def _extract_statistics(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Extract summary statistics from FastP JSON data."""
        summary = data.get("summary", {})
        before = summary.get("before_filtering", {})
        after = summary.get("after_filtering", {})
        duplication = data.get("duplication", {})
        insert_size = data.get("insert_size", {})
        filtering = data.get("filtering_result", {})
        
        # Basic info
        version = summary.get("fastp_version", "N/A")
        sequencing = summary.get("sequencing", "N/A")
        
        # Read lengths
        mean_length_before = f'{before.get("read1_mean_length", "N/A")}bp, {before.get("read2_mean_length", "N/A")}bp'
        mean_length_after = f'{after.get("read1_mean_length", "N/A")}bp, {after.get("read2_mean_length", "N/A")}bp'
        
        # Quality metrics
        dup_rate = duplication.get("rate", 0) * 100
        insert_peak = insert_size.get("peak", "N/A")
        
        # After-filtering stats
        total_reads = after.get("total_reads", 0)
        total_bases = after.get("total_bases", 0)
        q20_bases = after.get("q20_bases", 0)
        q30_bases = after.get("q30_bases", 0)
        q20_rate = after.get("q20_rate", 0) * 100
        q30_rate = after.get("q30_rate", 0) * 100
        gc_content = after.get("gc_content", 0) * 100
        
        # Filtering results
        total_reads_before = before.get("total_reads", 1)  # Avoid division by zero
        passed = filtering.get("passed_filter_reads", 0)
        low_quality = filtering.get("low_quality_reads", 0)
        too_many_N = filtering.get("too_many_N_reads", 0)
        too_short = filtering.get("too_short_reads", 0)
        
        # Calculate percentages
        reads_passed_pct = (passed / total_reads_before) * 100
        low_quality_pct = (low_quality / total_reads_before) * 100
        too_many_N_pct = (too_many_N / total_reads_before) * 100
        too_short_pct = (too_short / total_reads_before) * 100
        
        return {
            "fastp version": f"{version} (https://github.com/OpenGene/fastp)",
            "sequencing": sequencing,
            "mean length before filtering": mean_length_before,
            "mean length after filtering": mean_length_after,
            "duplication rate": f"{dup_rate:.2f}%",
            "Insert size peak": str(insert_peak),
            "total reads": f"{total_reads/1000:.1f} K",
            "total bases": f"{total_bases/1e6:.1f} M",
            "Q20 bases": f"{q20_bases/1e6:.1f} M ({q20_rate:.1f}%)",
            "Q30 bases": f"{q30_bases/1e6:.1f} M ({q30_rate:.1f}%)",
            "GC content": f"{gc_content:.1f}%",
            "reads passed filters": f"{passed/1000:.1f} K ({reads_passed_pct:.1f}%)",
            "reads with low quality": f"{low_quality/1000:.1f} K ({low_quality_pct:.1f}%)",
            "reads with too many N": f"{too_many_N} ({too_many_N_pct:.2f}%)",
            "reads too short": f"{too_short} ({too_short_pct:.2f}%)",
        }
    
    def create_summary_table(self, data: pd.DataFrame, **kwargs) -> pn.widgets.Tabulator:
        """Create a Panel Tabulator widget from FastP statistics."""
        table_name = kwargs.get("name", "FASTP Report Summary")
        
        table = pn.widgets.Tabulator(
            data, 
            layout='fit_columns', 
            show_index=False,
            name=table_name,
            pagination='local',
            page_size=20
        )
        
        return table