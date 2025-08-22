"""
Report sections with improved separation of concerns.
"""
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import pandas as pd
import panel as pn
import logging

from ..core.interfaces import ReportSection
from ..core.config import DefaultConfig
from ..processors.kraken_processor import KrakenProcessor, KrakenPlotGenerator
from ..processors.kaiju_processor import KaijuProcessor, KaijuPlotGenerator
from ..processors.blast_processor import BlastProcessor, BlastPlotGenerator
from ..processors.fastp_processor import FastpProcessor
from ..processors.flagstat_processor import FlagstatProcessor


class AlignmentStatsSection(ReportSection):
    """Report section for alignment statistics and read quality."""
    
    def __init__(self, config: Optional[DefaultConfig] = None):
        self.config = config or DefaultConfig()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @property
    def section_name(self) -> str:
        return "Alignment and Read Statistics"
    
    def generate_section(self, **kwargs) -> pn.Column:
        """Generate alignment statistics section."""
        flagstat_file = kwargs.get('flagstat_file')
        fastp_json = kwargs.get('fastp_json')
        secondary_flagstat_file = kwargs.get('secondary_flagstat_file')
        secondary_host = kwargs.get('secondary_host', 'Secondary')
        
        if not flagstat_file or not fastp_json:
            raise ValueError("flagstat_file and fastp_json are required")
        
        # Process alignment stats
        flagstat_processor = FlagstatProcessor(self.config.get_config('flagstat'))
        flagstat_data = flagstat_processor.process(flagstat_file)
        human_stats, human_pane = flagstat_processor.create_alignment_stats(flagstat_data, "Human")
        
        # Process secondary alignment if provided
        secondary_components = []
        if secondary_flagstat_file:
            secondary_data = flagstat_processor.process(secondary_flagstat_file)
            secondary_stats, secondary_pane = flagstat_processor.create_alignment_stats(
                secondary_data, secondary_host
            )
            secondary_components = [secondary_stats, pn.layout.Divider(), secondary_pane]
        
        # Process FastP data
        fastp_processor = FastpProcessor(self.config.get_config('fastp'))
        fastp_data = fastp_processor.process(fastp_json)
        fastp_table = fastp_processor.create_summary_table(fastp_data)
        
        # Create section layout
        header = self._create_header(
            """
            ## Alignment and Read Statistics
            Reads were aligned to Human and optionally other host species with bwa.
            """,
            height=80
        )
        
        alignment_components = [
            human_stats,
            pn.layout.Divider(),
            human_pane,
        ]
        alignment_components.extend(secondary_components)
        
        flagstat_column = pn.Column(*alignment_components, name="Alignment")
        tabs = pn.Tabs(flagstat_column, fastp_table)
        
        return pn.Column(header, tabs)
    
    def _create_header(self, text: str, height: int = 150) -> pn.pane.Markdown:
        """Create a styled header for the section."""
        return pn.pane.Markdown(
            text,
            styles={
                "color": "white",
                "padding": "10px",
                "text-align": "left",
                "font-size": "16px",
                "background": self.config.get("report.header_color", "#04c273"),
                "margin": "10px",
                "height": f"{height}px",
            }
        )


class RawClassificationSection(ReportSection):
    """Report section for raw read classification (Kraken and Kaiju)."""
    
    def __init__(self, config: Optional[DefaultConfig] = None):
        self.config = config or DefaultConfig()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @property
    def section_name(self) -> str:
        return "Classification of Raw Reads"
    
    def generate_section(self, **kwargs) -> pn.Column:
        """Generate raw classification section."""
        kraken_file = kwargs.get('kraken_file')
        kaiju_table = kwargs.get('kaiju_table')
        
        if not kraken_file or not kaiju_table:
            raise ValueError("kraken_file and kaiju_table are required")
        
        # Process Kraken data
        kraken_processor = KrakenProcessor(self.config.get_config('kraken'))
        kraken_plot_generator = KrakenPlotGenerator(self.config.get_config('plotting'))
        
        kraken_data = kraken_processor.process(kraken_file)
        
        # Create virus-only plot
        kraken_config = self.config.get_config('filtering.kraken')
        virus_data, virus_unclassified = kraken_processor.filter_data(
            kraken_data, virus_only=True, **kraken_config
        )
        virus_plot = kraken_plot_generator.generate_plot(
            virus_data, 
            title="Kraken Virus Classification",
            unclassified_pct=virus_unclassified
        ).interactive()
        
        # Create domain plot
        domain_data, domain_unclassified = kraken_processor.filter_data(
            kraken_data, level="domain", virus_only=False, **kraken_config
        )
        domain_plot = kraken_plot_generator.generate_plot(
            domain_data,
            title="Kraken Domain Classification",
            unclassified_pct=domain_unclassified
        ).interactive()
        
        # Process Kaiju data
        kaiju_processor = KaijuProcessor(self.config.get_config('kaiju'))
        kaiju_plot_generator = KaijuPlotGenerator(self.config.get_config('plotting'))
        
        kaiju_data = kaiju_processor.process(kaiju_table)
        kaiju_config = self.config.get_config('filtering.kaiju')
        kaiju_filtered, kaiju_unclassified = kaiju_processor.filter_data(kaiju_data, **kaiju_config)
        
        kaiju_plot = kaiju_plot_generator.generate_plot(
            kaiju_filtered,
            title="Kaiju Classification",
            unclassified_pct=kaiju_unclassified
        ).interactive()
        
        # Create section layout
        header = self._create_header(
            """
            ## Classification of Raw Reads
            Reads were classified with Kraken2 and Kaiju.
            """,
            height=80
        )
        
        kraken_virus_pane = pn.pane.Vega(virus_plot, sizing_mode="stretch_both", name="Kraken Virus Only")
        kraken_domain_pane = pn.pane.Vega(domain_plot, sizing_mode="stretch_both", name="Kraken All Domains")
        kaiju_pane = pn.pane.Vega(kaiju_plot, sizing_mode="stretch_both", name="Kaiju")
        
        tabs = pn.Tabs(kraken_virus_pane, kraken_domain_pane, kaiju_pane)
        
        return pn.Column(header, tabs)
    
    def _create_header(self, text: str, height: int = 150) -> pn.pane.Markdown:
        """Create a styled header for the section."""
        return pn.pane.Markdown(
            text,
            styles={
                "color": "white",
                "padding": "10px",
                "text-align": "left",
                "font-size": "16px",
                "background": self.config.get("report.header_color", "#04c273"),
                "margin": "10px",
                "height": f"{height}px",
            }
        )


class ContigClassificationSection(ReportSection):
    """Report section for contig classification (BLAST)."""
    
    def __init__(self, config: Optional[DefaultConfig] = None):
        self.config = config or DefaultConfig()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @property
    def section_name(self) -> str:
        return "Classification of Contigs"
    
    def generate_section(self, **kwargs) -> pn.Column:
        """Generate contig classification section."""
        blastn_file = kwargs.get('blastn_file')
        
        if not blastn_file:
            raise ValueError("blastn_file is required")
        
        # Process BLAST data
        blast_processor = BlastProcessor(self.config.get_config('blast'))
        blast_plot_generator = BlastPlotGenerator(self.config.get_config('plotting'))
        
        blast_data = blast_processor.process(blastn_file)
        blast_plot = blast_plot_generator.generate_plot(blast_data).interactive()
        
        # Create table for contig data
        table_data = blast_data.copy()
        if table_data.empty:
            table_data = pd.DataFrame({"sequence": ["NO SEQUENCES GENERATED"]})
        else:
            # Clean up table data
            columns_to_drop = ["name", "matches"]
            table_data = table_data.drop(columns=[col for col in columns_to_drop if col in table_data.columns])
        
        blast_table = pn.widgets.Tabulator(
            table_data,
            editors={'sequence': {'type': 'editable', 'value': False}},
            layout='fit_columns',
            pagination='local',
            page_size=15,
            show_index=False,
            name="Contig Table"
        )
        
        # Create section layout
        header = self._create_header(
            """
            ## Classification of Contigs
            #### Contigs generated by MEGAHIT were classified using BLASTN.
            #### To retrieve a sequence, copy (CTRL-C) the sequence column.
            """,
            height=120
        )
        
        blast_pane = pn.pane.Vega(blast_plot, sizing_mode="stretch_both", name="BLASTN")
        tabs = pn.Tabs(blast_pane, blast_table)
        
        return pn.Column(header, tabs)
    
    def _create_header(self, text: str, height: int = 150) -> pn.pane.Markdown:
        """Create a styled header for the section."""
        return pn.pane.Markdown(
            text,
            styles={
                "color": "white",
                "padding": "10px",
                "text-align": "left",
                "font-size": "16px",
                "background": self.config.get("report.header_color", "#04c273"),
                "margin": "10px",
                "height": f"{height}px",
            }
        )


class CoverageSection(ReportSection):
    """Report section for alignment coverage plots."""
    
    def __init__(self, config: Optional[DefaultConfig] = None):
        self.config = config or DefaultConfig()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @property
    def section_name(self) -> str:
        return "Alignment Coverage"
    
    def generate_section(self, **kwargs) -> pn.Column:
        """Generate coverage plots section."""
        coverage_folder = kwargs.get('coverage_folder')
        
        if not coverage_folder:
            raise ValueError("coverage_folder is required")
        
        coverage_path = Path(coverage_folder)
        coverage_plots = [
            x for x in coverage_path.iterdir()
            if x.suffix == ".svg" and not x.name.startswith("._")
        ]
        
        header = self._create_header("## Alignment Coverage", height=80)
        
        tabs = pn.Tabs()
        if coverage_plots:
            for plot_file in coverage_plots:
                name = plot_file.stem[:20]  # Truncate long names
                svg_pane = pn.pane.SVG(plot_file, sizing_mode='stretch_width', name=name)
                tabs.append(svg_pane)
            self.logger.info(f"Added {len(coverage_plots)} coverage plots to report")
        else:
            no_plots = pn.pane.Markdown("## No Coverage Plots Available", name="No Coverage Plots")
            tabs.append(no_plots)
            self.logger.warning("No coverage plots found")
        
        return pn.Column(header, tabs)
    
    def _create_header(self, text: str, height: int = 150) -> pn.pane.Markdown:
        """Create a styled header for the section."""
        return pn.pane.Markdown(
            text,
            styles={
                "color": "white",
                "padding": "10px",
                "text-align": "left",
                "font-size": "16px",
                "background": self.config.get("report.header_color", "#04c273"),
                "margin": "10px",
                "height": f"{height}px",
            }
        )