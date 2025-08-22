"""
Integration layer to connect enhanced visualizations with existing report system.
"""
from typing import Any, Dict, Optional, Union
from pathlib import Path
import pandas as pd
import panel as pn

from ..core.config import DefaultConfig
from ..processors.kraken_processor import KrakenProcessor
from ..processors.kaiju_processor import KaijuProcessor
from ..processors.blast_processor import BlastProcessor
from ..processors.fastp_processor import FastpProcessor
from ..processors.flagstat_processor import FlagstatProcessor

from .enhanced_plots import EnhancedKrakenPlotGenerator, EnhancedQualityPlotGenerator, ResponsiveDashboard
from .layout_engine import ResponsiveLayoutEngine, DashboardTemplates, InteractiveFeatures
from .config import VisualizationConfigManager, VisualizationConfig


class EnhancedReportGenerator:
    """Enhanced report generator with advanced visualizations."""
    
    def __init__(self, config: Optional[DefaultConfig] = None, 
                 viz_config: Optional[Union[str, VisualizationConfig]] = None):
        self.config = config or DefaultConfig()
        
        # Load visualization configuration
        if isinstance(viz_config, str):
            # Treat as preset name
            viz_manager = VisualizationConfigManager()
            self.viz_config = viz_manager.get_preset(viz_config)
        elif isinstance(viz_config, VisualizationConfig):
            self.viz_config = viz_config
        else:
            # Use default
            self.viz_config = VisualizationConfig()
        
        # Initialize components
        self.layout_engine = ResponsiveLayoutEngine(self.config.get_config())
        self.processors = self._initialize_processors()
        self.plot_generators = self._initialize_plot_generators()
    
    def _initialize_processors(self) -> Dict[str, Any]:
        """Initialize data processors."""
        return {
            "kraken": KrakenProcessor(self.config.get_config('kraken')),
            "kaiju": KaijuProcessor(self.config.get_config('kaiju')),
            "blast": BlastProcessor(self.config.get_config('blast')),
            "fastp": FastpProcessor(self.config.get_config('fastp')),
            "flagstat": FlagstatProcessor(self.config.get_config('flagstat'))
        }
    
    def _initialize_plot_generators(self) -> Dict[str, Any]:
        """Initialize enhanced plot generators."""
        return {
            "kraken": EnhancedKrakenPlotGenerator(self.viz_config.kraken.to_dict()),
            "kaiju": EnhancedKrakenPlotGenerator(self.viz_config.kaiju.to_dict()), 
            "quality": EnhancedQualityPlotGenerator(self.viz_config.quality.to_dict())
        }
    
    def generate_enhanced_report(self, **file_paths) -> pn.Column:
        """Generate report with enhanced visualizations."""
        # Process all data files
        processed_data = {}
        
        if "kraken_file" in file_paths:
            kraken_data = self.processors["kraken"].process(file_paths["kraken_file"])
            kraken_filtered, kraken_unclassified = self.processors["kraken"].filter_data(
                kraken_data, **self.config.get_config('filtering.kraken')
            )
            processed_data["kraken"] = (kraken_filtered, kraken_unclassified)
        
        if "kaiju_table" in file_paths:
            kaiju_data = self.processors["kaiju"].process(file_paths["kaiju_table"])
            kaiju_filtered, kaiju_unclassified = self.processors["kaiju"].filter_data(
                kaiju_data, **self.config.get_config('filtering.kaiju')
            )
            processed_data["kaiju"] = (kaiju_filtered, kaiju_unclassified)
        
        if "blast_file" in file_paths:
            blast_data = self.processors["blast"].process(file_paths["blast_file"])
            processed_data["blast"] = blast_data
        
        if "fastp_json" in file_paths:
            fastp_data = self.processors["fastp"].process(file_paths["fastp_json"])
            processed_data["fastp"] = fastp_data
        
        if "flagstat_file" in file_paths:
            flagstat_data = self.processors["flagstat"].process(file_paths["flagstat_file"])
            processed_data["flagstat"] = flagstat_data
        
        # Generate enhanced visualizations
        sections = self._create_enhanced_sections(processed_data, file_paths)
        
        # Apply layout template
        template_name = self.viz_config.layout.template.value
        if template_name == "scientific":
            return DashboardTemplates.scientific_report_template(sections)
        elif template_name == "executive":
            return DashboardTemplates.executive_dashboard_template(sections)
        elif template_name == "comparison":
            return DashboardTemplates.comparison_template(sections)
        else:
            # Default responsive layout
            return self._create_default_layout(sections)
    
    def _create_enhanced_sections(self, processed_data: Dict[str, Any], 
                                file_paths: Dict[str, str]) -> Dict[str, pn.pane.HTML]:
        """Create enhanced report sections with advanced visualizations."""
        sections = {}
        
        # Enhanced Classification Section
        if "kraken" in processed_data and "kaiju" in processed_data:
            kraken_data, kraken_unclassified = processed_data["kraken"]
            kaiju_data, kaiju_unclassified = processed_data["kaiju"]
            
            # Create comparison dashboard
            comparison_chart = ResponsiveDashboard.create_classification_dashboard(
                kraken_data, kaiju_data, "Classification Comparison"
            )
            sections["Classification Analysis"] = pn.pane.Vega(
                comparison_chart, 
                sizing_mode="stretch_both"
            )
            
            # Individual enhanced plots
            kraken_chart = self.plot_generators["kraken"].generate_plot(
                kraken_data,
                chart_type=self.viz_config.kraken.chart_type.value,
                title="Kraken Classification",
                unclassified_pct=kraken_unclassified
            )
            sections["Kraken Details"] = pn.pane.Vega(kraken_chart, sizing_mode="stretch_both")
            
            kaiju_chart = self.plot_generators["kaiju"].generate_plot(
                kaiju_data,
                chart_type=self.viz_config.kaiju.chart_type.value,
                title="Kaiju Classification", 
                unclassified_pct=kaiju_unclassified
            )
            sections["Kaiju Details"] = pn.pane.Vega(kaiju_chart, sizing_mode="stretch_both")
        
        # Enhanced Quality Metrics
        if "fastp" in processed_data:
            fastp_data = processed_data["fastp"]
            
            # Create quality dashboard
            quality_metrics = self._extract_quality_metrics(fastp_data)
            quality_chart = self.plot_generators["quality"].generate_plot(
                quality_metrics,
                chart_type=self.viz_config.quality.chart_type.value,
                title="Quality Assessment"
            )
            sections["Quality Metrics"] = pn.pane.Vega(quality_chart, sizing_mode="stretch_both")
        
        # Enhanced Alignment Statistics
        if "flagstat" in processed_data:
            flagstat_data = processed_data["flagstat"]
            alignment_stats, alignment_chart = self.processors["flagstat"].create_alignment_stats(
                flagstat_data, "Host"
            )
            
            # Combine statistics and enhanced chart
            combined_section = pn.Column(alignment_stats, alignment_chart)
            sections["Alignment Statistics"] = combined_section
        
        # Coverage Analysis (if available)
        if "coverage_folder" in file_paths:
            coverage_section = self._create_coverage_section(file_paths["coverage_folder"])
            sections["Coverage Analysis"] = coverage_section
        
        # Add interactive controls if enabled
        if self.viz_config.layout.show_filters:
            filter_controls = InteractiveFeatures.add_filter_controls(
                ["domain", "species", "percent"]
            )
            sections["Data Filters"] = filter_controls
        
        if self.viz_config.layout.show_export:
            export_controls = InteractiveFeatures.create_export_controls()
            sections["Export Tools"] = export_controls
        
        return sections
    
    def _create_default_layout(self, sections: Dict[str, pn.pane.HTML]) -> pn.Column:
        """Create default responsive layout."""
        # Convert sections to cards
        cards = []
        for title, content in sections.items():
            card = self.layout_engine.create_card_layout(title, content)
            cards.append(card)
        
        # Create responsive grid
        grid = self.layout_engine.create_adaptive_grid(
            cards, 
            grid_type=str(self.viz_config.layout.grid_columns)
        )
        
        return grid
    
    def _extract_quality_metrics(self, fastp_data: pd.DataFrame) -> pd.DataFrame:
        """Extract quality metrics for gauge/radar visualization."""
        # Extract key quality metrics from fastp data
        metrics = []
        
        for _, row in fastp_data.iterrows():
            metric_name = row["Metric"]
            value_str = row["Value"]
            
            # Parse percentage values
            if "%" in value_str and "Q20" in metric_name:
                value = float(value_str.split("(")[1].split("%")[0]) / 100
                metrics.append({
                    "metric": "Q20 Quality",
                    "value": value,
                    "min_val": 0,
                    "max_val": 1,
                    "threshold": 0.8
                })
            elif "%" in value_str and "Q30" in metric_name:
                value = float(value_str.split("(")[1].split("%")[0]) / 100
                metrics.append({
                    "metric": "Q30 Quality", 
                    "value": value,
                    "min_val": 0,
                    "max_val": 1,
                    "threshold": 0.7
                })
            elif "%" in value_str and "duplication" in metric_name.lower():
                value = float(value_str.split("%")[0]) / 100
                metrics.append({
                    "metric": "Duplication Rate",
                    "value": 1 - value,  # Invert so higher is better
                    "min_val": 0,
                    "max_val": 1,
                    "threshold": 0.9
                })
        
        return pd.DataFrame(metrics) if metrics else pd.DataFrame()
    
    def _create_coverage_section(self, coverage_folder: str) -> pn.pane.HTML:
        """Create enhanced coverage visualization section."""
        coverage_path = Path(coverage_folder)
        coverage_plots = [
            x for x in coverage_path.iterdir()
            if x.suffix == ".svg" and not x.name.startswith("._")
        ]
        
        if coverage_plots:
            # Create tabbed interface for coverage plots
            tabs = []
            for plot_file in coverage_plots[:10]:  # Limit to first 10 plots
                name = plot_file.stem[:25]  # Truncate long names
                svg_content = pn.pane.SVG(plot_file, sizing_mode="stretch_width")
                
                # Wrap in card
                card = self.layout_engine.create_card_layout(
                    f"Coverage: {name}", svg_content, "info"
                )
                tabs.append((name, card))
            
            return self.layout_engine.create_tabbed_interface(tabs, tab_location="above")
        else:
            return pn.pane.Markdown("## No Coverage Plots Available")


def create_visualization_examples() -> None:
    """Create example visualization configurations."""
    from .config import create_example_configs
    create_example_configs()
    
    print("Created example visualization configurations in config_examples/")
    print("Available configurations:")
    print("- visualization_scientific.json")
    print("- visualization_executive.json") 
    print("- visualization_minimal.json")
    print("- visualization_publication.json")
    print("- visualization_comprehensive.json")