"""
Main report generator using MVC pattern with improved architecture.
"""
from typing import Optional, Union
from pathlib import Path
import panel as pn
import logging

from ..core.config import DefaultConfig
from ..core.exceptions import ReportGenerationError
from .sections import (
    AlignmentStatsSection,
    RawClassificationSection, 
    ContigClassificationSection,
    CoverageSection
)


class ReportGenerator:
    """Main report generator with MVC architecture."""
    
    def __init__(self, config: Optional[DefaultConfig] = None):
        self.config = config or DefaultConfig()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize Panel extensions
        self._setup_panel()
        
        # Initialize sections
        self.sections = {
            "alignment": AlignmentStatsSection(self.config),
            "raw_classification": RawClassificationSection(self.config),
            "contig_classification": ContigClassificationSection(self.config),
            "coverage": CoverageSection(self.config)
        }
    
    def _setup_panel(self) -> None:
        """Configure Panel settings."""
        try:
            pn.extension("tabulator")
            pn.extension("vega", sizing_mode="stretch_width", template=self.config.get("report.template", "fast"))
            pn.widgets.Tabulator.theme = self.config.get("report.theme", "modern")
        except Exception as e:
            self.logger.error(f"Failed to setup Panel extensions: {e}")
            raise ReportGenerationError(f"Panel setup failed: {e}")
    
    def generate_report(self,
                       blastn_file: Union[str, Path],
                       kraken_file: Union[str, Path],
                       kaiju_table: Union[str, Path],
                       fastp_json: Union[str, Path],
                       flagstat_file: Union[str, Path],
                       coverage_folder: Union[str, Path],
                       secondary_flagstat_file: Optional[Union[str, Path]] = None,
                       secondary_host: Optional[str] = None,
                       sample_name: Optional[str] = None) -> pn.Column:
        """Generate the complete report."""
        
        try:
            sample_name = sample_name or "Sample"
            self.logger.info(f"Starting report generation for sample: {sample_name}")
            
            # Generate each section
            alignment_section = self.sections["alignment"].generate_section(
                flagstat_file=flagstat_file,
                fastp_json=fastp_json,
                secondary_flagstat_file=secondary_flagstat_file,
                secondary_host=secondary_host
            )
            
            raw_classification_section = self.sections["raw_classification"].generate_section(
                kraken_file=kraken_file,
                kaiju_table=kaiju_table
            )
            
            contig_classification_section = self.sections["contig_classification"].generate_section(
                blastn_file=blastn_file
            )
            
            coverage_section = self.sections["coverage"].generate_section(
                coverage_folder=coverage_folder
            )
            
            # Create main layout
            header = self._create_main_header(sample_name)
            
            main_tabs = pn.Tabs(
                ("Alignment Stats", alignment_section),
                ("Classification of Raw Reads", raw_classification_section),
                ("Classification of Contigs", contig_classification_section),
                ("Alignment Coverage", coverage_section),
                tabs_location="left",
            )
            
            report = pn.Column(header, pn.layout.Divider(), main_tabs)
            
            self.logger.info(f"Report generation completed for sample: {sample_name}")
            return report
            
        except Exception as e:
            self.logger.error(f"Report generation failed: {e}")
            raise ReportGenerationError(f"Failed to generate report: {e}")
    
    def _create_main_header(self, sample_name: str) -> pn.pane.Markdown:
        """Create the main report header."""
        return pn.pane.Markdown(
            f"""
            # ReportHanter Report
            ## Report of {sample_name}
            """,
            styles={
                "color": "white",
                "padding": "10px",
                "text-align": "center",
                "font-size": "20px",
                "background": self.config.get("report.header_bg_color", "#011a01"),
                "margin": "10px",
                "height": "185px",
            }
        )
    
    def save_report(self, 
                   report: pn.Column, 
                   output_path: Union[str, Path], 
                   title: Optional[str] = None) -> None:
        """Save the report to an HTML file."""
        try:
            title = title or "ReportHanter Report"
            report.save(str(output_path), title=title)
            self.logger.info(f"Report saved to: {output_path}")
        except Exception as e:
            self.logger.error(f"Failed to save report to {output_path}: {e}")
            raise ReportGenerationError(f"Failed to save report: {e}")